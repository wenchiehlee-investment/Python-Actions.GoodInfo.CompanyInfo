# Taiwan Stock Industry & Market Info Fetcher

This project provides Python scripts to fetch and consolidate official industry classifications and market types (Listed, OTC, Emerging, Public) for Taiwan stocks. It uses the official [TWSE ISIN system](https://isin.twse.com.tw/isin/C_public.jsp) as the source of truth.

## Features

*   **Comprehensive Coverage:** Fetches data across four markets:
    *   **TWSE (上市):** Stock Exchange Main Board
    *   **TPEX (上櫃):** Over-the-Counter
    *   **Emerging (興櫃):** Emerging Stock Board
    *   **Public (公開發行):** Public Companies not yet listed on the above
*   **Data Enrichment:** Takes a simple list of Stock IDs and appends:
    *   **Market Type (市場別):** e.g., 上市, 上櫃, 興櫃, 公開發行
    *   **Industry Category (產業別):** e.g., 半導體業, 電子零組件業
*   **Robust Handling:** Handles specific encoding (`Big5`) and SSL certificate issues associated with the TWSE ISIN website.

## Prerequisites

*   Python 3.8+
*   Required Python packages:

```bash
pip install pandas requests lxml
```

## Usage

### 1. Prepare/Update the Stock List
Optionally, run the helper script to download the latest "Observation List" and "Focus List" from the source repository:

```bash
python Get觀察名單.py
```
*This updates `StockID_TWSE_TPEX.csv`.*

### 2. Fetch Company Information
Run the main script to scrape official data and generate the report:

```bash
python FetchCompanyInfo.py
```

## Output Format
The script generates **`raw_companyinfo.csv`** containing:

| Header | Description | Example |
| :--- | :---------- | :------ |
| `代號` | Stock ID (e.g., `2330`) | `2330` |
| `名稱` | Company Name (e.g., `台積電`) | `台積電` |
| `市場別` | Market Type (上市, 上櫃, 興櫃, 公開發行) | `上市` |
| `產業別` | Industry Category (e.g., 半導體業) | `半導體業` |
| `ETF_0050_權重` | Weight in ETF 0050 (%) | `47.5` |
| `ETF_0056_權重` | Weight in ETF 0056 (%) | `2.5` |
| `主要業務` | **Main Business** (Scraped from GoodInfo) | `晶圓代工...` |
| `相關概念` | **Related Concepts** (Scraped from GoodInfo) | `Apple概念股...` |
| `相關集團` | **Related Group** (Scraped from GoodInfo) | `台積電集團` |

## GoodInfo Scraping
The script uses **Selenium** with a headless Chrome browser to bypass anti-scraping measures on GoodInfo. This allows it to retrieve:
*   **Main Business (主要業務)**
*   **Related Concepts (相關概念)**
*   **Related Group (相關集團)**

*Note: This process adds significant runtime (approx. 5-10 seconds per stock).*

## Technical Notes

*   **Source:** Data is scraped from `isin.twse.com.tw` using Modes 1, 2, 4, and 5.
*   **Priority:** If a stock ID exists in multiple tables (rare), priority is given in order: TWSE > TPEX > Emerging > Public.
*   **Encoding:** The TWSE ISIN site uses `Big5` encoding, which is explicitly handled in the script to prevent mojibake.