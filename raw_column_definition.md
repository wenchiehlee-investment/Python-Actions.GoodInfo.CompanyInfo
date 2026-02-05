---
source: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.CompanyInfo/refs/heads/main/raw_column_definition.md
destination: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/refs/heads/main/raw_column_definition.md
---

# Column Definitions for raw_companyinfo.csv

This table defines the structure and source of data in `raw_companyinfo.csv`.

| Column | Description | Source |
| :--- | :--- | :--- |
| `代號` | Taiwan Stock ID (e.g., 2330) | Local Input / TWSE ISIN |
| `名稱` | Company Name | Local Input / TWSE ISIN |
| `市場別` | Market Type (上市, 上櫃, 興櫃, 公開發行) | TWSE ISIN |
| `產業別` | Industry Category | TWSE ISIN |
| `市值` | Market Capitalization (兆/億) | GoodInfo (Summary Table) |
| `市值佔大盤比重` | Weight in TAIEX Index (%) | TAIFEX Futures QA Detail |
| `ETF_0050_權重` | Weight in Yuanta/P-shares Taiwan Top 50 ETF (%) | MoneyDJ constituent data |
| `ETF_0056_權重` | Weight in Yuanta/P-shares Taiwan Dividend Plus ETF (%) | MoneyDJ constituent data |
| `ETF_00878_權重` | Weight in Cathay MSCI Taiwan ESG Sustainability High Dividend Yield ETF (%) | MoneyDJ constituent data |
| `ETF_00919_權重` | Weight in Capital Taiwan High Dividend ETF (%) | MoneyDJ constituent data |
| `主要業務` | Detailed description of the company's main operations | GoodInfo |
| `nVidia概念` | Mark "1" if part of Nvidia supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Google概念` | Mark "1" if part of Google supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Amazon概念` | Mark "1" if part of Amazon supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Meta概念` | Mark "1" if part of Meta supply chain/concept | GoodInfo / Gemini AI Analysis |
| `OpenAI概念` | Mark "1" if part of OpenAI supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Microsoft概念` | Mark "1" if part of Microsoft supply chain/concept | GoodInfo / Gemini AI Analysis |
| `AMD概念` | Mark "1" if part of AMD supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Apple概念` | Mark "1" if part of Apple supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Oracle概念` | Mark "1" if part of Oracle supply chain/concept | GoodInfo / Gemini AI Analysis |
| `SanDisk概念` | Mark "1" if part of SanDisk supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Qualcomm概念` | Mark "1" if part of Qualcomm supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Micro概念` | Mark "1" if part of Micron Technology supply chain/concept | GoodInfo / Gemini AI Analysis |
| `SanDisk概念` | Mark "1" if part of SanDisk supply chain/concept | GoodInfo / Gemini AI Analysis |
| `相關集團` | Name of the business group the company belongs to | GoodInfo (Group List mapping) |
