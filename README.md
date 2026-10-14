# Afficionado Coffee Roasters — Premium Analytics Dashboard

## Run on Windows
1. Extract this folder.
2. Open Command Prompt inside `Afficionado_Coffee_Forecasting`.
3. Run `python -m venv .venv` (skip if you already created one).
4. Activate: `.venv\Scripts\activate`
5. Install: `python -m pip install -r requirements.txt`
6. Start: `python -m streamlit run app.py`

## Features
- Dark and light theme switch (dark is default)
- Interactive filters for store location, category and product type
- Executive KPIs and insight cards
- Category revenue donut chart and category-to-product treemap
- Product popularity vs revenue bubble/quadrant analysis
- Pareto cumulative revenue analysis
- Peak-hour demand chart, store comparison, data quality and CSV exports
- Reads the provided Excel workbook from `data/Afficionado Coffee Roasters.xlsx` by default

## Data limitation
The workbook's Transactions sheet includes year and time-of-day but no actual calendar date. The app therefore provides descriptive and peak-hour analytics, but does not invent dates or claim daily forecasting. Add a true `transaction_date` or `transaction_datetime` field to enable forecasting.
