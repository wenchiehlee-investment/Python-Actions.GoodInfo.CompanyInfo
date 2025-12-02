import pandas as pd
import requests
import urllib3
from io import StringIO

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== 設定 ====
INPUT_CSV = "StockID_TWSE_TPEX.csv"
OUTPUT_CSV = "raw_companyinfo.csv"

BASE_URL = "https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_isin_table(mode: int, market_label: str) -> pd.DataFrame:
    """
    mode = 2 → TWSE（上市）
    mode = 4 → TPEX（上櫃/興櫃）
    market_label = 'TWSE' 或 'TPEX'
    """
    url = BASE_URL.format(mode=mode)
    res = requests.get(url, headers=HEADERS, timeout=20, verify=False)
    res.encoding = "big5"

    df = pd.read_html(StringIO(res.text))[0]

    df.columns = df.iloc[0]
    df = df.iloc[1:].copy()

    df = df.rename(
        columns={
            "有價證券代號及名稱": "代號名稱",
            "上市日": "上市日",
            "市場別": "市場別",
            "產業別": "產業別",
        }
    )

    # 保留代號開頭為數字者
    df = df[df["代號名稱"].astype(str).str.match(r"^\d+")].copy()

    # 拆代號與名稱
    df["代號"] = df["代號名稱"].str.extract(r"^(\d+)")
    df["名稱_官方"] = df["代號名稱"].str.replace(r"^\d+", "", regex=True).str.strip()

    return df[["代號", "名稱_官方", "市場別", "產業別", "上市日"]]


def main():
    # 1) 讀 base CSV
    base = pd.read_csv(INPUT_CSV, dtype={"代號": str})
    base["代號"] = base["代號"].astype(str).str.strip()

    # 2) 抓 TWSE + TPEX 官方資料
    print("下載 TWSE（上市）資料...")
    twse_raw = fetch_isin_table(2, "TWSE")

    print("下載 TPEX（上櫃）資料...")
    tpex_raw = fetch_isin_table(4, "TPEX")

    print("下載 Emerging（興櫃）資料...")
    emg_raw = fetch_isin_table(5, "Emerging")

    print("下載 Public（公開發行）資料...")
    # Mode 1 has different columns, so we fetch separately or adjust fetch_isin_table
    # But fetch_isin_table expects "市場別" which Mode 1 lacks.
    # Let's modify fetch_isin_table to handle missing "市場別" or handle it here.
    # Actually, simpler to just use fetch_isin_table and let it fail/warn? 
    # No, fetch_isin_table renames "市場別" which doesn't exist.
    # Let's manually fetch Mode 1 here to avoid breaking the helper function.
    
    url_pub = BASE_URL.format(mode=1)
    res_pub = requests.get(url_pub, headers=HEADERS, timeout=20, verify=False)
    res_pub.encoding = "big5"
    pub_df = pd.read_html(StringIO(res_pub.text))[0]
    pub_df.columns = pub_df.iloc[0]
    pub_df = pub_df.iloc[1:].copy()
    
    # Mode 1 Columns: 有價證券代號及名稱, 國際證券辨識號碼..., 公開發行日, 產業別, ...
    pub_df = pub_df.rename(
        columns={
            "有價證券代號及名稱": "代號名稱",
            "產業別": "產業別_PUB",
        }
    )
    # Filter stocks
    pub_df = pub_df[pub_df["代號名稱"].astype(str).str.match(r"^\d+")].copy()
    pub_df["代號"] = pub_df["代號名稱"].str.extract(r"^(\d+)")
    pub_df["市場別_PUB"] = "公開發行" # Manually assign
    
    pub = pub_df[["代號", "市場別_PUB", "產業別_PUB"]]

    # === 產生 TWSE 欄位 ===
    twse = twse_raw.rename(
        columns={
            "市場別": "市場別_TWSE",
            "產業別": "產業別_TWSE",
        }
    )[
        [
            "代號",
            "市場別_TWSE",
            "產業別_TWSE",
        ]
    ]

    # === 產生 TPEX 欄位 ===
    tpex = tpex_raw.rename(
        columns={
            "市場別": "市場別_TPEX",
            "產業別": "產業別_TPEX",
        }
    )[
        [
            "代號",
            "市場別_TPEX",
            "產業別_TPEX",
        ]
    ]

    # === 產生 Emerging 欄位 ===
    emg = emg_raw.rename(
        columns={
            "市場別": "市場別_EMG",
            "產業別": "產業別_EMG",
        }
    )[
        [
            "代號",
            "市場別_EMG",
            "產業別_EMG",
        ]
    ]

    # 3) 合併
    merged = base.merge(twse, on="代號", how="left")
    merged = merged.merge(tpex, on="代號", how="left")
    merged = merged.merge(emg, on="代號", how="left")
    merged = merged.merge(pub, on="代號", how="left")

    # === 合併欄位 ===
    # 優先順序: TWSE > TPEX > Emerging > Public
    merged["市場別"] = (
        merged["市場別_TWSE"]
        .fillna(merged["市場別_TPEX"])
        .fillna(merged["市場別_EMG"])
        .fillna(merged["市場別_PUB"])
    )
    merged["產業別"] = (
        merged["產業別_TWSE"]
        .fillna(merged["產業別_TPEX"])
        .fillna(merged["產業別_EMG"])
        .fillna(merged["產業別_PUB"])
    )

    # 4) 欄位順序
    col_order = [
        "代號",
        "名稱",
        "市場別",
        "產業別",          # This serves as '相關產業'
        "主要業務",
        "相關概念",
        "相關集團",
    ]

    # Add empty columns for data that cannot be reliably scraped
    merged["主要業務"] = None
    merged["相關概念"] = None
    merged["相關集團"] = None

    for c in merged.columns:
        if c not in col_order and c not in [
            "市場別_TWSE", "產業別_TWSE", 
            "市場別_TPEX", "產業別_TPEX", 
            "市場別_EMG", "產業別_EMG",
            "市場別_PUB", "產業別_PUB",
            "上市日_TWSE"
        ]:
            # 排除已合併的原始欄位，保留其他可能的額外欄位
            col_order.append(c)

    merged = merged[col_order]

    # 5) 存檔
    merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n=== 已完成 ===")
    print(f"輸出：{OUTPUT_CSV}")

    print("\n=== 最終欄位 ===")
    for col in merged.columns:
        print(col)

    print("\n=== Sample Row ===")
    if not merged.empty:
        print(merged.iloc[0])



if __name__ == "__main__":
    main()
