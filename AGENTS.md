# Repository Guidelines

## Project Structure & Module Organization
- `FetchCompanyInfo.py` is the main data pipeline (ISIN lookups, ETF weights, GoodInfo scraping).
- `Get觀察名單.py` downloads the latest watchlists from GitHub.
- `StockID_TWSE_TPEX.csv` and `StockID_TWSE_TPEX_focus.csv` are source inputs.
- `raw_companyinfo.csv` is the generated output artifact.
- `DESIGNDOC.md` and `GEMINI.md` document design and Gemini-specific notes.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs Python dependencies.
- `python Get觀察名單.py` refreshes watchlist CSVs from the remote source.
- `python FetchCompanyInfo.py` runs the full enrichment pipeline and writes `raw_companyinfo.csv`.
- Selenium requires a local Chrome install (the script uses headless Chrome via `webdriver-manager`).

## Coding Style & Naming Conventions
- Use 4-space indentation and standard Python naming (snake_case for functions, PascalCase for classes if added).
- Keep script entry points in `if __name__ == "__main__":` blocks.
- Prefer descriptive CSV column headers aligned with existing files (e.g., `ETF_0050_權重`).

## Testing Guidelines
- No automated test suite is present. If you add tests, place them under a new `tests/` directory and name files `test_*.py`.
- For manual validation, run the pipeline and confirm `raw_companyinfo.csv` headers and row counts.

## Commit & Pull Request Guidelines
- Recent commit messages use prefixes like `feat:`, `ci:`, `data:`, and `Auto-update:`; follow the same pattern.
- Include concise summaries of data or scraping changes and note any output file updates.
- If modifying scraping behavior, mention target sources (e.g., `isin.twse.com.tw`, GoodInfo, MoneyDJ).

## Security & Configuration Tips
- GoodInfo scraping is rate-sensitive; avoid parallel requests and expect 5–10s per stock.
- Do not commit credentials or API keys; keep any secrets in environment variables or local files ignored by Git.
