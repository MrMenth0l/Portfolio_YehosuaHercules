# Project Summary

This Git repo currently contains one active Python project, [`fx-var-usdgtq/`](./fx-var-usdgtq), plus high-level portfolio planning docs in [`Docs/`](./Docs). The live codebase estimates 1-day 99% VaR for USD/GTQ by downloading Banguat FX data, building deterministic FX/PnL features, training Stage 4 baseline models, and writing artifacts under `data/` and `reports/`.

## Repository Map

- `fx-var-usdgtq/src/`: production code. `pipeline.py` orchestrates the full run; `io.py`, `features.py`, and `model.py` own the core logic.
- `fx-var-usdgtq/tests/`: pytest suite for IO, feature engineering, model smoke tests, and pipeline behavior.
- `fx-var-usdgtq/data/`: raw/processed/external data roots plus `DATA_VERSION.md`. Most contents are generated and gitignored except placeholder files.
- `fx-var-usdgtq/reports/`: generated predictions, figures, JSON, and PDFs. Treat as output, not source.
- `fx-var-usdgtq/notebooks/`: placeholder only; production logic should stay in `src/`.
- `Docs/`: broader GT-Quant portfolio guidance. Useful for product context, but it references sibling projects that are not present in this repo snapshot.

## Commands

Run Python work from `fx-var-usdgtq/`. `pytest` relies on `pyproject.toml` setting `pythonpath = ["."]`, so running tests from the outer repo root will give the wrong import context.

```bash
cd fx-var-usdgtq
python3 -m venv .venv
source .venv/bin/activate
make install
make lint
make test
make run
```

Targeted checks:

```bash
cd fx-var-usdgtq
./.venv/bin/pytest tests/test_io.py -q
./.venv/bin/pytest tests/test_pipeline_stage3.py -q
./.venv/bin/python -m src.pipeline
```

There is no separate build step, typechecker, or CI workflow configured in the repo.

## Conventions

- Keep production logic in `fx-var-usdgtq/src/`; do not move core behavior into notebooks.
- Preserve strict raw/processed schema ordering: `date,rate`. `src/io.py` rejects extra columns or reordered schemas.
- Feature frames must keep `date` sorted ascending, unique, and free of NaNs. `pnl_next_day` is the required prediction target.
- Time splitting is chronological and fixed-window: the last `250` rows form the test window by default.
- Central paths and pipeline constants live in `fx-var-usdgtq/src/config.py`; update config constants instead of scattering new literal paths through the code.
- The pipeline is intentionally thin: refresh raw data, persist snapshots, build features, train three baseline models, and write predictions.

## Validation Before Handoff

- Minimum after code changes: `cd fx-var-usdgtq && make lint && make test`
- If you touch `src/io.py`, `src/pipeline.py`, model artifact names, or output paths, also run `cd fx-var-usdgtq && make run` and verify the expected files under `data/raw/`, `data/processed/`, and `reports/`
- Prefer targeted pytest files first when changing a single module, then finish with the full test suite

## Warnings and Guardrails

- `make run` always refreshes data from the live Banguat SOAP endpoint in `src/config.py`. The default range is pinned to `1900-01-01` through `2026-02-22`, with up to 8 retries per yearly chunk and a 300 second request timeout, so end-to-end runs are network-bound and can take a while.
- Generated artifacts are mostly ignored by git: `data/raw/*`, `data/processed/*`, `data/external/*`, and `reports/*.csv|*.json|*.pdf|reports/figures/*.png`. Do not hand-edit them unless the task is specifically about fixtures or generated outputs.
- The checked-in local environment at `fx-var-usdgtq/.venv` is Python `3.14.3`, while `pyproject.toml` targets `py311` for Ruff and Black. If you hit version-specific behavior, rebuild the venv on Python 3.11 before debugging deeper.
- `Docs/agent.md` and `Docs/gt_quant_portfolio_guidelines.md` are planning documents for a broader portfolio. Use them for intent and standards, not as proof that missing directories or deliverables already exist.

## Related Docs

- [`fx-var-usdgtq/README.md`](./fx-var-usdgtq/README.md)
- [`fx-var-usdgtq/data/DATA_VERSION.md`](./fx-var-usdgtq/data/DATA_VERSION.md)
- [`Docs/agent.md`](./Docs/agent.md)
