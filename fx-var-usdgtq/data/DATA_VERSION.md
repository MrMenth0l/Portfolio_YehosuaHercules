# DATA_VERSION

- Project: `fx-var-usdgtq`
- Source name: Banco de Guatemala (Banguat) SOAP service
- Source endpoint: `https://banguat.gob.gt/variables/ws/TipoCambio.asmx`
- SOAP action: `http://www.banguat.gob.gt/variables/ws/TipoCambioRango`
- Retrieval method: HTTP `POST` SOAP request, parsed from XML `<Var>` nodes
- Snapshot file: `data/raw/usd_gtq_daily.csv`
- Raw schema (strict): `date` (ISO `YYYY-MM-DD`), `rate` (float, mapped from Banguat `venta`)
- Processed file: `data/processed/fx_rates.parquet`
- Default retrieval range policy:
  - `start_date`: `1900-01-01` (full-history request mode)
  - `end_date`: `2026-02-22` (pinned for reproducibility)
- Run metadata file (ignored by git): `data/raw/usd_gtq_daily.metadata.json`
  - includes retrieval timestamp, requested range, row count, min/max date, schema, and SHA-256 of raw CSV
- Notes:
  - Pipeline refreshes data on every `make run`.
  - Raw snapshot preserves all rows returned by source (including weekends/holidays).
