import requests
import pandas as pd
from io import StringIO
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_etf_weights(etf_id):
    """
    Fetches ETF constituents and weights from MoneyDJ.
    Returns a dictionary: { 'StockID': 'Weight%' }
    Example: { '2330': '47.5' }
    """
    # Basic0007B seems to be the "All Holdings" view
    url = f"https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={etf_id}.TW"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Fetching ETF {etf_id} weights from MoneyDJ...")
    try:
        res = requests.get(url, headers=headers, timeout=20, verify=False)
        res.encoding = "utf-8"
        
        # Parse tables
        dfs = pd.read_html(StringIO(res.text))
        
        target_df = None
        for df in dfs:
            # Look for column headers
            cols = df.columns.astype(str)
            if "個股名稱" in cols and "投資比例(%)" in cols:
                target_df = df
                break
        
        if target_df is None:
            print(f"Warning: Constituent table not found for ETF {etf_id}")
            return {}
            
        weights = {}
        for _, row in target_df.iterrows():
            name_col = str(row["個股名稱"])
            weight_col = row["投資比例(%)"]
            
            # Parse Stock ID from "Name(ID.TW)"
            # Example: "台積電(2330.TW)"
            match = re.search(r'\((\d+)\.TW\)', name_col)
            if match:
                stock_id = match.group(1)
                # Convert weight to string, handle NaN
                if pd.isna(weight_col):
                    w_str = ""
                else:
                    w_str = str(weight_col).strip()
                
                weights[stock_id] = w_str
        
        print(f"  -> Retrieved {len(weights)} constituents for ETF {etf_id}")
        return weights

    except Exception as e:
        print(f"Error fetching ETF {etf_id}: {e}")
        return {}

if __name__ == "__main__":
    # Test
    w50 = fetch_etf_weights("0050")
    print("0050 Sample:", list(w50.items())[:3])
    
    w56 = fetch_etf_weights("0056")
    print("0056 Sample:", list(w56.items())[:3])
