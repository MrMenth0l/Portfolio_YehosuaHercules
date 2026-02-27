# FX VaR USD/GTQ (Stage 3)

## Problem statement
This project estimates and backtests 1-day 99% VaR for USD/GTQ exposure in a reproducible pipeline.

## Current status
Stage 3 is implemented for data acquisition, cleaning, and feature engineering:
- downloads USD/GTQ from official Banguat SOAP endpoint,
- writes strict raw snapshot (`date,rate`),
- builds deterministic return/PnL feature frame with no NaNs,
- writes feature dataset to `data/processed/features.parquet`,
- writes run metadata sidecar with retrieval details.

Modeling, backtesting metrics, plots, and Spanish PDF reporting are still pending later stages.

## Data source and schema
- Source: Banco de Guatemala SOAP `TipoCambioRango`
- Endpoint: `https://banguat.gob.gt/variables/ws/TipoCambio.asmx`
- Field mapping: `fecha -> date`, `venta -> rate`
- Strict schema:
  - `date`: datetime (stored as ISO date in CSV)
  - `rate`: numeric

## Reproducibility defaults
- Default `start_date`: `1900-01-01` (full-history request mode)
- Default `end_date`: `2026-02-22` (pinned)
- Pipeline always refreshes raw data on run.

## Stage 3 feature engineering
- Returns:
  - `return_simple = rate / rate.shift(1) - 1`
  - `return_log = log(rate / rate.shift(1))`
- PnL:
  - `pnl = 10000 * return_simple`
  - `pnl_next_day = pnl.shift(-1)` (target)
- Calendar feature:
  - `is_weekend` (0/1)
- Lag and rolling windows:
  - lags/windows: `1, 5, 10, 20, 60`
  - lagged returns and pnl
  - rolling mean/volatility on simple returns
- NaN policy:
  - warm-up and tail rows are dropped so final feature frame has no NaNs.

## How to run
```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make lint
make test
make run
```

## Stage 3 outputs
- `data/raw/usd_gtq_daily.csv`
- `data/raw/usd_gtq_daily.metadata.json` (gitignored)
- `data/processed/features.parquet`
- structured `STAGE3_FEATURES` summary line printed by `python -m src.pipeline`

## Next steps
- Stage 4/5: historical + Monte Carlo VaR model training and backtesting metrics
- Stage 6: Spanish one-page PDF report generation
