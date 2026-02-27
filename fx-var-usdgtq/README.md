# FX VaR USD/GTQ (Stage 4)

## Problem statement
This project estimates and backtests 1-day 99% VaR for USD/GTQ exposure in a reproducible pipeline.

## Current status
Stage 4 is implemented for data acquisition, feature engineering, and baseline modeling:
- downloads USD/GTQ from official Banguat SOAP endpoint,
- writes strict raw snapshot (`date,rate`),
- builds deterministic return/PnL feature frame with no NaNs,
- writes feature dataset to `data/processed/features.parquet`,
- trains and saves three baseline models (`quantile-linear`, `quantile-tree`, `linear-mean`),
- writes test-window prediction table to `reports/fx-var_usdgtq_predictions.csv`,
- writes run metadata sidecar with retrieval details.

Backtesting metrics, plots, and Spanish PDF reporting are still pending later stages.

## Data source and schema
- Source: Banco de Guatemala SOAP `TipoCambioRango`
- Endpoint: `https://banguat.gob.gt/variables/ws/TipoCambio.asmx`
- Field mapping: `fecha -> date`, `venta -> rate`
- Strict schema:
  - `date`: datetime (stored as ISO date in CSV)
  - `rate`: numeric

## Reproducibility and timeout policy
- Default `start_date`: `1900-01-01` (full-history request mode)
- Default `end_date`: `2026-02-22` (pinned)
- Pipeline always refreshes raw data on run.
- SOAP timeout is intentionally large for robustness (`300s` per attempt).
- Per-year chunk retries: up to `8` attempts with exponential backoff (`2s` to `120s` cap).

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

## Stage 4 baseline models
- Target: `pnl_next_day`
- Split: fixed last `250` rows for test window
- Feature matrix: all numeric Stage-3 columns except `date` and `pnl_next_day`
- Models:
  - linear quantile regression (`q=0.01`)
  - tree quantile regression (`q=0.01`)
  - linear mean regression

## How to run
```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make lint
make test
make run
```

## Stage 4 outputs
- `data/raw/usd_gtq_daily.csv`
- `data/raw/usd_gtq_daily.metadata.json` (gitignored)
- `data/processed/features.parquet`
- `data/processed/models/qr_linear_q01.joblib`
- `data/processed/models/qr_tree_q01.joblib`
- `data/processed/models/linear_mean.joblib`
- `reports/fx-var_usdgtq_predictions.csv`
- structured `STAGE4_MODELS` summary line printed by `python -m src.pipeline`

## Next steps
- Stage 5: historical + Monte Carlo VaR backtesting metrics and reports/metrics.json
- Stage 6: Spanish one-page PDF report generation
