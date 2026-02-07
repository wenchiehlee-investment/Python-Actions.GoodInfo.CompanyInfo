# Python-Actions.GoodInfo.CompanyInfo

## Project Overview

This project is a Python-based automation tool designed to fetch, consolidate, and update Taiwan stock market data (TWSE and TPEX). It primarily focuses on maintaining a "Watchlist" of companies by enriching a base list of stock IDs with official industry categories, market types, ETF weights, and detailed business info scraped from GoodInfo.

### Key Features
*   **Watchlist Synchronization:** Downloads the latest "Observation List" (`StockID_TWSE_TPEX.csv`) and "Focus List" from a remote GitHub repository.
*   **Data Enrichment:** Scrapes official market data (Market Type, Industry Category) from `isin.twse.com.tw`.
*   **ETF Data:** Fetches portfolio weights for **0050**, **0056**, **00878**, and **00919** ETFs from MoneyDJ.
*   **TAIFEX Data:** Fetches market cap weight relative to TAIEX from TAIFEX website.
*   **GoodInfo Scraping:** Uses **Selenium** to scrape detailed "Main Business" and "Related Concepts" from GoodInfo, and bulk-maps "Related Groups" from the Group List page.
*   **Gemini AI Analysis:** Uses Gemini API for AI-powered concept stock identification for tech giants.
*   **Data Consolidation:** Merges all data into a comprehensive CSV report.

## Directory Structure

*   `FetchCompanyInfo.py`: The main data processing script. Consolidates logic for ISIN fetching, ETF weights, and Selenium scraping.
*   `Get觀察名單.py`: A utility script to download the latest stock watchlists.
*   `StockID_TWSE_TPEX.csv`: The input CSV file containing the base list of stock IDs and names.
*   `raw_companyinfo.csv`: The generated output file containing the enriched company information.

## Building and Running

### Prerequisites
Ensure you have Python installed along with the following dependencies:

```bash
pip install pandas requests lxml urllib3 html5lib selenium webdriver-manager google-genai python-dotenv
```
*(Note: `google-chrome-stable` must be installed on the system for Selenium)*

**Environment Variables:**
*   `GOOGLE_API_KEY`: Required for Gemini AI concept analysis (optional feature)

### Usage

1.  **Update Watchlists:**
    First, download the latest stock lists to ensure you have the most current `StockID_TWSE_TPEX.csv`.
    ```bash
    python Get觀察名單.py
    ```

2.  **Fetch and Enrich Data:**
    Run the main script to fetch official data and generate the final report.
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
| `市值` | **Market Cap** (Scraped from GoodInfo) | `15.5兆` |
| `市值佔大盤比重` | **TAIEX Weight** (%) | `43.09%` |
| `ETF_0050_權重` | Weight in ETF 0050 (%) | `47.5` |
| `ETF_0056_權重` | Weight in ETF 0056 (%) | `2.5` |
| `ETF_00878_權重` | Weight in ETF 00878 (%) | `3.2` |
| `ETF_00919_權重` | Weight in ETF 00919 (%) | `1.8` |
| `主要業務` | **Main Business** (Scraped from GoodInfo) | `晶圓代工...` |
| `nVidia概念` | Concept Breakdown (1 if matched) | `1` |
| `Google概念` | Concept Breakdown (1 if matched) | `1` |
| `Amazon概念` | Concept Breakdown (1 if matched) | `1` |
| `Meta概念` | Concept Breakdown (1 if matched) | `1` |
| `OpenAI概念` | Concept Breakdown (1 if matched) | `1` |
| `Microsoft概念` | Concept Breakdown (1 if matched) | `1` |
| `AMD概念` | Concept Breakdown (1 if matched) | `1` |
| `Apple概念` | Concept Breakdown (1 if matched) | `1` |
| `Oracle概念` | Concept Breakdown (1 if matched) | `1` |
| `Micro概念` | Concept Breakdown (1 if matched) | `1` |
| `Qualcomm概念` | Concept Breakdown (1 if matched) | `1` |
| `Lenovo概念` | Concept Breakdown (1 if matched) | `1` |
| `Dell概念` | Concept Breakdown (1 if matched) | `1` |
| `HP概念` | Concept Breakdown (1 if matched) | `1` |
| `相關集團` | **Related Group** (Bulk Mapped from GoodInfo) | `台積電集團` |

## GoodInfo Scraping
The script uses **Selenium** with a headless Chrome browser to bypass anti-scraping measures on GoodInfo.
*   **Group Mapping:** First, it visits the "Group Stocks" list to build a map of all stocks belonging to specific business groups.
*   **Detail Scraping:** Then, it visits each stock's detail page to extract "Main Business", "Market Cap", and "Related Concepts".
*   **Concept Breakdown:** Finally, it parses the "Related Concepts" to populate the specific tech giant columns.

*Note: This process adds significant runtime (approx. 5-10 seconds per stock).*

## Architecture

### Data Flow
1.  `Get觀察名單.py` downloads `StockID_TWSE_TPEX.csv` (base watchlist) from remote GitHub repo
2.  `FetchCompanyInfo.py` enriches this data:
    *   Fetches official TWSE/TPEX/Emerging/Public market data via ISIN API
    *   Scrapes GoodInfo for business details using Selenium (headless Chrome)
    *   Retrieves ETF weights from MoneyDJ
    *   Fetches TAIEX weights from TAIFEX
    *   Optionally uses Gemini API for concept stock analysis
3.  Outputs `raw_companyinfo.csv` with consolidated data

### Key Technical Details
*   **Encoding:** TWSE ISIN responses use `big5` encoding. Output CSVs use `utf-8-sig` for Excel compatibility.
*   **SSL:** TWSE ISIN API requires `verify=False` due to certificate issues.
*   **Concept Flag System:** `CONCEPT_KEYWORDS` dict in `FetchCompanyInfo.py` maps column names to keyword lists. Binary flags (1/0) are generated for each tech giant (nVidia, Google, Amazon, Meta, OpenAI, Microsoft, AMD, Apple, Oracle, Micron, SanDisk, Qualcomm, Lenovo, Dell, HP).
*   **Rate Limiting:**
    *   GoodInfo scraping has 3-second delays between requests
    *   Gemini API uses exponential backoff (3, 6, 12, 24, 48 seconds) for 503/rate limit errors
    *   Consecutive GoodInfo failures (5+) triggers early abort to avoid IP blocks

## GitHub Actions

The workflow (`.github/workflows/Actions.yaml`) runs daily at 16:00 Taipei time (08:00 UTC):
1.  Installs Chrome and Python dependencies
2.  Runs `Get觀察名單.py` then `FetchCompanyInfo.py`
3.  Auto-commits updated CSV files to main branch
