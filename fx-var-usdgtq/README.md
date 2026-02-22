# FX VaR USD/GTQ (Stage 2)

## Problem statement
This project estimates and backtests 1-day 99% VaR for USD/GTQ exposure in a reproducible pipeline.

## Current status
Stage 2 is implemented for data acquisition and snapshotting:
- downloads USD/GTQ from official Banguat SOAP endpoint,
- writes strict raw snapshot (`date,rate`),
- writes processed Parquet dataset,
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
- Pipeline always refreshes on run.

## How to run
```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make lint
make test
make run
```

## Stage 2 outputs
- `data/raw/usd_gtq_daily.csv`
- `data/raw/usd_gtq_daily.metadata.json` (gitignored)
- `data/processed/fx_rates.parquet`
- structured summary line printed by `python -m src.pipeline`

## Next steps
- Stage 3: cleaning/feature engineering for returns and P&L
- Stage 4/5: historical + Monte Carlo VaR and backtesting metrics
- Stage 6: Spanish one-page PDF report generation
