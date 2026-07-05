# Nifty 100 Financial Intelligence Platform

A 45-day data analytics capstone project that builds a financial intelligence system for Nifty 100 companies using Python, SQLite, Excel reports and analytics modules.

## Completed Sprints

### Sprint 1 — Data Foundation
- Loaded 7 core datasets and 5 supporting datasets.
- Built SQLite database: `data/db/nifty100.db`.
- Created validation outputs, load audit and manual review report.

### Sprint 2 — Financial Ratio Engine
- Implemented profitability, leverage, efficiency, CAGR and cash flow KPIs.
- Populated `financial_ratios` table with 1,100+ company-year rows.
- Generated capital allocation output and ratio edge-case log.
- Added KPI unit tests.

### Sprint 3 — Screener + Peer Engine
- Built custom filter engine and 6 preset screeners.
- Generated `output/screener_output.xlsx` with 6 sheets.
- Computed peer percentile rankings for all 11 peer groups.
- Populated `peer_percentiles` table in SQLite.
- Generated radar charts and `output/peer_comparison.xlsx`.

## Project Structure

```text
nifty100_financial_platform/
├── config/
├── data/
│   ├── raw/
│   └── db/
├── db/
├── output/
├── reports/
│   └── radar_charts/
├── src/
│   ├── analytics/
│   ├── etl/
│   └── screener/
└── tests/
```

## Setup

```bash
pip install -r requirements.txt
```

## Main Commands

```bash
python src/etl/load_to_db.py
python src/analytics/ratio_engine.py
python src/screener/presets.py
python src/screener/export.py
python src/analytics/peer.py
python src/analytics/radar.py
python src/analytics/peer_report.py
pytest
```

## Key Outputs

- `output/load_audit.csv`
- `output/validation_failures.csv`
- `output/capital_allocation.csv`
- `output/ratio_edge_cases.log`
- `output/screener_output.xlsx`
- `output/peer_comparison.xlsx`
- `reports/radar_charts/`

## Sprint 3 Validation

All preset screeners return between 5 and 50 companies. Peer comparison workbook contains exactly 11 sheets, and all Sprint 3 tests pass.
