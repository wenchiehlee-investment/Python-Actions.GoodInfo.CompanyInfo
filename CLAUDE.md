# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taiwan stock market data automation tool that fetches and consolidates company information from multiple sources:
- **TWSE/TPEX ISIN database** (isin.twse.com.tw) - Official market type and industry categories
- **GoodInfo** (via Selenium) - Main business, market cap, related concepts, and group affiliations
- **MoneyDJ** - ETF constituent weights (0050, 0056, 00878, 00919)
- **TAIFEX** - Market cap weight relative to TAIEX
- **Gemini API** - AI-powered concept stock identification for tech giants

## Commands

```bash
# Install dependencies
pip install pandas requests lxml urllib3 html5lib selenium webdriver-manager google-genai python-dotenv

# Download latest stock watchlists from GitHub
python Get觀察名單.py

# Fetch and enrich company data (main script)
python FetchCompanyInfo.py
```

## Architecture

### Data Flow
1. `Get觀察名單.py` downloads `StockID_TWSE_TPEX.csv` (base watchlist) from remote GitHub repo
2. `FetchCompanyInfo.py` enriches this data:
   - Fetches official TWSE/TPEX/Emerging/Public market data via ISIN API
   - Scrapes GoodInfo for business details using Selenium (headless Chrome)
   - Retrieves ETF weights from MoneyDJ
   - Optionally uses Gemini API for concept stock analysis
3. Outputs `raw_companyinfo.csv` with consolidated data

### Key Technical Details

**Encoding**: TWSE ISIN responses use `big5` encoding. Output CSVs use `utf-8-sig` for Excel compatibility.

**SSL**: TWSE ISIN API requires `verify=False` due to certificate issues.

**Concept Flag System**: `CONCEPT_KEYWORDS` dict in `FetchCompanyInfo.py` maps column names to keyword lists. The `build_concept_flags()` function parses the `相關概念` field to populate binary flag columns (1/0) for each tech giant (nVidia, Google, Amazon, Meta, OpenAI, Microsoft, AMD, Apple, Oracle, Micron, SanDisk, Qualcomm, Lenovo, Dell, HP).

**Rate Limiting**:
- GoodInfo scraping has 3-second delays between requests
- Gemini API uses exponential backoff (3, 6, 12, 24, 48 seconds) for 503/rate limit errors
- Consecutive GoodInfo failures (5+) triggers early abort to avoid IP blocks

**Environment Variables**: `GOOGLE_API_KEY` required for Gemini concept analysis (optional feature).

## GitHub Actions

The workflow (`.github/workflows/Actions.yaml`) runs daily at 16:00 Taipei time:
1. Installs Chrome and Python dependencies
2. Runs `Get觀察名單.py` then `FetchCompanyInfo.py`
3. Auto-commits updated CSV files to main branch
