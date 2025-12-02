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
| `主要業務` | **Main Business** (Currently empty due to scraping limitations) | |
| `相關概念` | **Related Concepts** (Currently empty due to scraping limitations) | |
| `相關集團` | **Related Group** (Currently empty due to scraping limitations) | |

## Limitations
Due to the strong anti-scraping protection employed by websites like GoodInfo (e.g., JavaScript challenges, browser checks), it is not feasible to automatically extract "主要業務" (Main Business), "相關概念" (Related Concepts), and "相關集團" using simple HTTP requests in this environment. These columns are included in the output CSV but will remain empty. Manual data entry or a more complex, browser-automation-based solution (which is beyond the scope of this script's design) would be required to populate them.

## Technical Notes

*   **Source:** Data is scraped from `isin.twse.com.tw` using Modes 1, 2, 4, and 5.
*   **Priority:** If a stock ID exists in multiple tables (rare), priority is given in order: TWSE > TPEX > Emerging > Public.
*   **Encoding:** The TWSE ISIN site uses `Big5` encoding, which is explicitly handled in the script to prevent mojibake.