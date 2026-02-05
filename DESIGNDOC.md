# Design Document: Taiwan Stock Info Fetcher

This document outlines the architecture, logic, and automation strategy for the `Python-Actions.GoodInfo.CompanyInfo` project.

## 1. Objective
To enrich a local list of Taiwan Stock IDs (`StockID_TWSE_TPEX.csv`) with official **Market Type**, **Industry Category**, **Market Cap**, **ETF Weights**, and detailed **Business Info** (including Groups and Concept Breakdown) fetched from multiple sources.

## 2. System Architecture

### Data Flow
1.  **Input:** `StockID_TWSE_TPEX.csv` (Columns: `代號`, `名稱`)
2.  **Fetch (Official):** Query `isin.twse.com.tw` for Market/Industry data (Modes 1, 2, 4, 5).
3.  **Fetch (ETF):** Query `MoneyDJ` for 0050/0056/00878/00919 constituents and weights.
4.  **Fetch (GoodInfo):** Use **Selenium** to:
    *   Visit the "Group List" page to map stocks to groups.
    *   Visit individual stock pages to scrape "Main Business", "Market Cap", and "Concepts" (used for concept flags only).
5.  **Merge:** Consolidate all data into a single DataFrame.
6.  **Post-Process:** Breakdown "Related Concepts" into individual boolean columns.
7.  **Output:** `raw_companyinfo.csv`.

## 3. Script Logic (`FetchCompanyInfo.py`)

### 3.1. Dependencies
*   `requests`: HTTP client for static pages (ISIN, MoneyDJ).
*   `pandas`: Data manipulation.
*   `selenium`: Browser automation for GoodInfo.
*   `webdriver_manager`: Chrome driver management.
*   `google-genai`: (Optional) Gemini API for concept analysis.

### 3.2. Data Sources

#### TWSE ISIN (Market & Industry)
*   **URL:** `https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}`
*   **Modes:** 2 (Listed), 4 (OTC), 5 (Emerging), 1 (Public).
*   **Strategy:** `requests` + `pandas.read_html`.

#### MoneyDJ (ETF Weights)
*   **URL:** `https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={id}.TW`
*   **IDs:** 0050, 0056, 00878, 00919.
*   **Strategy:** `requests` + `pandas.read_html`.

#### TAIFEX (Market Cap Weight)
*   **URL:** `https://www.taifex.com.tw/cht/9/futuresQADetail`
*   **Data:** TAIEX Index Weights (市值佔大盤比重).
*   **Strategy:** `requests` + `pandas.read_html`.

#### GoodInfo (Business, Concepts, Groups, Market Cap)
*   **Group Map:** Visits `https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=集團股` first. Iterates *all* group links to build a global `{StockID: GroupName}` map.
*   **Stock Details:** Visits `https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={id}`.
    *   **Wait Strategy:** Waits for `<body>` and `<td>` elements to ensure JS rendering.
*   **Extraction:** Regex parsing of the rendered HTML source to extract "Main Business", "Related Concepts", and "Market Cap" (the raw `相關概念` text is not written to output).

### 3.3. Merge Strategy
*   **Market/Industry:** Coalesced from TWSE > TPEX > Emerging > Public.
*   **ETF:** Mapped from MoneyDJ data.
*   **GoodInfo:** Direct assignment from scrape/map results.

### 3.4. Post-Processing (Concept Breakdown)
*   **Logic:** The script iterates through a predefined list of Tech Giants:
    *   `["nVidia", "Google", "Amazon", "Meta", "OpenAI", "Microsoft", "AMD", "Apple", "Oracle", "Micron", "SanDisk", "Qualcomm", "Lenovo"]`
*   **Action:** Creates a new column for each giant (e.g., `nVidia概念`).
*   **Value:** If the giant's name appears in the scraped `相關概念` string (case-insensitive), the column is marked with "1", otherwise "0".


## 4. GitHub Actions Automation

*   **Schedule:** Daily at 16:00 Taipei Time (08:00 UTC).
*   **Environment:** `ubuntu-latest`.
*   **Steps:**
    1.  Install Python dependencies (`selenium`, etc.).
    2.  Install `google-chrome-stable`.
    3.  Run `Get觀察名單.py` (Update list).
    4.  Run `FetchCompanyInfo.py` (Main process).
    5.  Commit and push `raw_companyinfo.csv`.
*   **Sync:** A separate workflow syncs the result to the Analyzer repository at 17:00 Taipei Time.
