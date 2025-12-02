# Design Document: Taiwan Stock Info Fetcher

This document outlines the architecture, logic, and automation strategy for the `Python-Actions.GoodInfo.CompanyInfo` project. It allows developers or AI agents to regenerate the codebase or set up CI/CD pipelines.

## 1. Objective
To enrich a local list of Taiwan Stock IDs (`StockID_TWSE_TPEX.csv`) with official **Market Type** (上市/上櫃/興櫃/公開發行) and **Industry Category** (產業別) data fetched from the Taiwan Stock Exchange (TWSE) ISIN database.

## 2. System Architecture

### Data Flow
1.  **Input:** `StockID_TWSE_TPEX.csv` (Columns: `代號`, `名稱`)
2.  **Fetch:** Query `https://isin.twse.com.tw/isin/C_public.jsp` for multiple market modes.
3.  **Process:**
    *   Parse HTML tables into Pandas DataFrames.
    *   Clean and normalize column names.
    *   Filter for valid stock records.
4.  **Merge:** Join official data with the input list using `代號` (Stock ID) as the key.
5.  **Output:** `raw_companyinfo.csv` (Columns: `代號`, `名稱`, `市場別`, `產業別`, `ETF_0050`, `ETF_0056`, `主要業務`, `相關概念`, `相關集團`).

## 3. Script Logic (`FetchCompanyInfo.py`)

### 3.1. Dependencies
*   `requests`: HTTP client.
*   `pandas`: Data manipulation and HTML table parsing.
*   `urllib3`: Used to suppress SSL warnings.
*   `io.StringIO`: To wrap HTML text for Pandas reading.
*   `GetETFWeights.py`: Helper module to fetch ETF composition.

### 3.2. Data Sources

#### TWSE ISIN (Market & Industry)
Data fetched from `https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}`.

| Mode | Market Type | Description | Note |
| :--- | :--- | :--- | :--- |
| **2** | TWSE (上市) | Main Board | Standard handling. |
| **4** | TPEX (上櫃) | OTC Market | Standard handling. |
| **5** | Emerging (興櫃) | Emerging Stock | Needed for stocks like `6035`. |
| **1** | Public (公開發行) | Public Companies | Needed for stocks like `6699`. Unique column structure. |

#### MoneyDJ (ETF Weights)
Data fetched from `https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={id}.TW`.
*   **0050:** Yuanta Taiwan 50
*   **0056:** Yuanta Taiwan High Dividend Yield
*   *Note:* We use `Basic0007B` which provides the full list of constituents (e.g., Top 50) rather than the summary page.

### 3.3. Implementation Details
*   **SSL/TLS:** The TWSE server often has certificate issues.
    *   *Action:* `requests.get(..., verify=False)`
    *   *Action:* `urllib3.disable_warnings(...)` to keep logs clean.
*   **Encoding:** The response is in `Big5`.
    *   *Action:* Explicitly set `res.encoding = 'big5'` before parsing.
*   **Merge Strategy:**
    *   Perform Left Joins from the Input CSV against all 4 dataframes.
    *   **Coalesce Logic:** `市場別 = TWSE.fillna(TPEX).fillna(Emerging).fillna(Public)`
    *   This ensures that if a stock moves markets, the most "senior" market status is preferred (though IDs are usually unique).
*   **GoodInfo Data (主要業務, 相關概念, 相關集團):** These columns are requested but cannot be reliably scraped.
    *   *Action:* Columns `主要業務`, `相關概念`, `相關集團` are added to the DataFrame but are initialized with `None` (empty) values. This is due to the strong anti-scraping measures employed by GoodInfo (JavaScript challenges) which prevent automated data extraction using simple `requests` in this environment.

### 3.4. Public Company (Mode 1) Handling
Mode 1 tables lack the standard `市場別` column found in Modes 2/4/5.
*   **Logic:** Manually assign string literal `"公開發行"` to `市場別` column after fetching Mode 1 data.

## 4. GitHub Actions Automation

To automate the daily/weekly updates of this data, use the following workflow configuration.

### File Path: `.github/workflows/update_company_info.yml`

```yaml
name: Update Company Info

on:
  schedule:
    # Run every day at 00:00 UTC (08:00 Taipei Time)
    - cron: '0 0 * * *'
  workflow_dispatch: # Allow manual trigger

permissions:
  contents: write

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas requests lxml urllib3

      - name: Update Stock Lists (Optional)
        run: python Get觀察名單.py

      - name: Fetch Official Company Info
        run: python FetchCompanyInfo.py

      - name: Commit and Push changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "Auto-update: Company Info & Lists"
          file_pattern: "*.csv"
```

## 5. Future Improvements
*   **GoodInfo Data Extraction:** If "主要業務", "相關概念", and "相關集團" are critical, a more advanced solution involving headless browser automation (e.g., Selenium, Playwright) would be required to bypass GoodInfo's anti-scraping measures. This would significantly increase the complexity and resource requirements of the workflow.
*   **Anti-Scraping:** If TWSE adds stricter blocking, consider adding retry logic with exponential backoff or rotating User-Agents (though currently `verify=False` + standard headers works).
*   **GoodInfo Integration:** If "Main Business" text is strictly required, integrate a headless browser (e.g., Selenium/Playwright) solution, though this significantly increases runtime overhead.
