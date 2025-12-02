# Python-Actions.GoodInfo.CompanyInfo

## Project Overview

This project is a Python-based automation tool designed to fetch, consolidate, and update Taiwan stock market data (TWSE and TPEX). It primarily focuses on maintaining a "Watchlist" of companies by enriching a base list of stock IDs with official industry categories and market types fetched directly from the Taiwan Stock Exchange (TWSE) ISIN database.

### Key Features
*   **Watchlist Synchronization:** Downloads the latest "Observation List" (`StockID_TWSE_TPEX.csv`) and "Focus List" from a remote GitHub repository.
*   **Data Enrichment:** Scrapes official market data (Market Type, Industry Category, Listing Date) from `isin.twse.com.tw`.
*   **Data Consolidation:** Merges the base watchlist with the official data to produce a comprehensive CSV report.

## Directory Structure

*   `FetchCompanyInfo.py`: The main data processing script. It reads the local `StockID_TWSE_TPEX.csv`, fetches official data from TWSE/TPEX, merges the information, and outputs `StockID_TWSE_TPEX_官方產業精簡版.csv`.
*   `Get觀察名單.py`: A utility script to download the latest stock watchlists from the `wenchiehlee/GoPublic` GitHub repository.
*   `StockID_TWSE_TPEX.csv`: The input CSV file containing the base list of stock IDs and names.
*   `StockID_TWSE_TPEX_官方產業精簡版.csv`: The generated output file containing the enriched company information.

## Building and Running

### Prerequisites
Ensure you have Python installed along with the following dependencies:

```bash
pip install pandas requests lxml
```
*(Note: `lxml` or `html5lib` is typically required by `pandas.read_html`)*

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

### Output
The process will generate `StockID_TWSE_TPEX_官方產業精簡版.csv` in the same directory, containing columns like:
*   `代號` (Stock ID)
*   `名稱` (Name)
*   `市場別_TWSE` / `市場別_TPEX` (Market Type)
*   `產業別_TWSE` / `產業別_TPEX` (Industry Category)
*   `上市日_TWSE` (Listing Date)

## Development Conventions

*   **Encoding:** Scripts and CSVs use `utf-8` (or `utf-8-sig` for Excel compatibility).
    *   *Note:* `FetchCompanyInfo.py` uses `big5` encoding when decoding responses from `isin.twse.com.tw` to correctly handle Traditional Chinese text.
*   **Data Sources:**
    *   **TWSE (Listed):** Mode 2 on `isin.twse.com.tw`. SSL verification is explicitly disabled (`verify=False`) due to certificate issues on the TWSE server.
    *   **TPEX (OTC/Emerging):** Mode 4 on `isin.twse.com.tw`
*   **Error Handling:** Basic error handling is implemented for network requests. `FetchCompanyInfo.py` assumes the input CSV exists.
