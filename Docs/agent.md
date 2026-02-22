# Codex Agent Task — GT-Quant Portfolio (General Repository)
**Purpose:** You are an engineering agent working inside a single “general” repository that contains three subprojects:
1) `cpi-nowcast-gt/` (CPI nowcast),
2) `credit-pd-ifrs9-demo/` (Credit PD + mini IFRS-9 ECL),
3) `fx-var-usdgtq/` (FX VaR).

Your job is to implement **production-ish** code (Python), tests, and reproducible pipelines so each subproject can be run end-to-end and produce a 1-page PDF report.

---

## 0) Hard Rules (Non-negotiables)
### 0.1 Output language policy
- **Code, comments, function names:** English.
- **User-facing artifacts (PDF reports, README “Executive summary” snippets):** Spanish.
- **File/column names:** English unless the upstream dataset forces Spanish.

### 0.2 No hallucinations / no fake numbers
- Do **NOT** invent metric values, dataset sizes, data ranges, or sources.
- Every number shown in a report must be computed by code and persisted under `reports/`.
- If data is missing or unclear, fail fast with an explicit error message in the pipeline output.

### 0.3 No notebook-only logic
- Notebooks are optional for exploration, but the “real” implementation must live in `src/`.
- Pipelines must be runnable from CLI / module entrypoint.

### 0.4 Deterministic & reproducible
- Fix seeds (`numpy`, `random`, model library seeds).
- Ensure sorted time indices.
- Ensure stable train/valid/test splitting.
- Avoid non-deterministic operations unless explicitly controlled.

### 0.5 Minimal, clean, testable code
- Prefer simple functions over large classes.
- Each module should be importable and unit-testable.
- Keep pipelines short and orchestrate calls to pure functions.

---

## 1) Repository Structure (General Repo)
Implement this structure (or align to it if already present):

```
gt-quant-portfolio/
  common/
    README.md
    make_common.mk              # optional shared make rules
    src_common/
      time_utils.py
      paths.py
      reporting.py              # optional helpers for PDF build
  cpi-nowcast-gt/
    (standard per-project template)
  credit-pd-ifrs9-demo/
    (standard per-project template)
  fx-var-usdgtq/
    (standard per-project template)
```

Each project folder must follow:

```
project/
  data/
    raw/              # gitignored
    processed/        # gitignored
    external/         # optional
    DATA_VERSION.md
  notebooks/          # optional
  src/
    __init__.py
    config.py
    io.py
    features.py
    model.py
    metrics.py
    plots.py
    pipeline.py
  tests/
    test_io.py
    test_features.py
    test_metrics.py
    test_model_smoke.py
  reports/
    figures/
    metrics.json
    report.pdf
  README.md
  requirements.txt
  Makefile
  pyproject.toml      # recommended
```

---

## 2) Common Build Standards (All Projects)
### 2.1 Makefile targets (minimum)
- `install`: install dependencies from requirements.txt
- `lint`: `ruff check .` and `black --check .`
- `test`: `pytest -q`
- `run`: run pipeline (e.g., `python -m src.pipeline`)

### 2.2 Python version & libraries
- Python: 3.11+
- Minimum libs: `pandas`, `numpy`, `matplotlib`, `scipy`, `scikit-learn`, `statsmodels`, `pytest`, `ruff`, `black`
- Project B adds: `xgboost` or `lightgbm` (pick one, justify in README)
- If additional libs are required, add them explicitly and justify in README.

### 2.3 Data policy
- Do not commit large raw datasets to git.
- Put data snapshots under `data/raw/` (gitignored) and document them in `DATA_VERSION.md`.
- Pipelines should support:
  - reading local snapshots, and
  - (optional) downloading data with a script, if the source is stable.

---

## 3) “One Command” Pipeline Contract (Per Project)
Each project must provide a runnable module command:

- `python -m src.pipeline`

It must:
1. Create output directories (`reports/`, `reports/figures/`, `data/processed/`).
2. Load raw data (or error with instructions if missing).
3. Clean & feature engineer.
4. Train baseline model (and improved model where applicable).
5. Evaluate & save metrics to `reports/metrics.json`.
6. Generate plots to `reports/figures/*.png`.
7. Generate a **1-page** `reports/report.pdf` in **Spanish**.

**If any stage fails**, raise a clear exception with actionable guidance.

---

## 4) Testing Requirements (Per Project)
### 4.1 Minimum tests
- `test_io.py`
  - validates schema presence (expected columns)
  - validates date parsing (if applicable)
- `test_features.py`
  - checks shape, no unintended NaNs, sorted dates (time series)
- `test_metrics.py`
  - metric functions verified on toy arrays with known outputs
- `test_model_smoke.py`
  - training returns a model-like object
  - prediction length matches input length
  - predictions contain no NaNs

### 4.2 Coverage target
- Aim for **≥ 70% coverage on `src/`** (best-effort).
- Do not game coverage; prioritize meaningful unit tests.

---

## 5) Project-Specific Requirements

## 5A) CPI Nowcast — `cpi-nowcast-gt/`
### Goal
Nowcast Guatemala CPI (monthly) using a SARIMAX baseline and rolling-origin evaluation.

### Data (minimum)
- Monthly CPI time series with:
  - `date` (monthly period or month-end)
  - `cpi` (numeric)

### Feature engineering
- Must enforce monthly frequency.
- Must include seasonality controls:
  - month dummies OR sin/cos month encoding.
- Optional: simple exogenous regressors if reliably available.

### Model
- Baseline: SARIMAX (statsmodels)
  - seasonal period = 12
  - clear parameterization documented in README

### Evaluation
- Rolling-origin backtest:
  - sequentially fit on data up to time `t`, predict `t+1`
- Metric: MAPE
  - Save MAPE and prediction table.

### Outputs
- `reports/predictions.csv` with: `date,y_true,y_pred,abs_pct_error`
- `reports/metrics.json` includes:
  - `mape_last_12m`
  - overall rolling MAPE
- Plots:
  - actual vs predicted (recent window)
  - error over time (optional)
- 1-page report in Spanish:
  - what CPI is, what nowcasting means, method bullets, metric table, key chart

---

## 5B) Credit PD + Mini IFRS-9 ECL — `credit-pd-ifrs9-demo/`
### Goal
Train PD model (probability of default) and compute a mini ECL demo.

### Data (minimum)
- Tabular dataset with:
  - binary target: `default` (0/1)
  - feature columns (mixed numeric/categorical)

### Modeling
- Baseline: Logistic Regression
- Improved: Gradient boosting (XGBoost or LightGBM)
- Must handle categorical variables (one-hot is acceptable).

### Evaluation
- ROC-AUC
- KS statistic
- Calibration (reliability curve)
- Save confusion matrix thresholding is optional, but if included must be clearly defined.

### ECL demo (mini)
- Produce sample ECL table:
  - `account_id` (can be generated index if not present)
  - `pd` (model prediction)
  - `lgd` (constant, e.g., 0.45, or simple segment rule)
  - `ead` (balance or amount; use a real column if present)
  - `stage` (simple rule; document)
  - `ecl = pd * lgd * ead`
- Save: `reports/ecl_sample.csv`
- Add summary totals: total ECL, by stage.

### Outputs
- `reports/metrics.json` includes: `roc_auc`, `ks`, calibration summary
- Plots:
  - ROC curve
  - calibration curve
  - PD distribution by class (optional)
- 1-page report in Spanish:
  - explain PD and ECL conceptually, show performance metrics, show ECL totals

---

## 5C) FX VaR — `fx-var-usdgtq/`
### Goal
Compute 1-day 99% VaR for USD/GTQ and backtest it.

### Data (minimum)
- Daily USD/GTQ exchange rate with:
  - `date`
  - `rate` or `close`

### Returns & P&L
- Choose return type: log returns or simple % returns (document choice).
- Define a notional for P&L (e.g., $10,000 exposure); keep configurable.

### VaR methods
- Historical VaR (quantile of rolling window P&L)
- Monte Carlo VaR:
  - Either Normal assumption (mu/sigma from window) or bootstrap.
  - Must be deterministic with seed.

### Backtest
- Rolling window (e.g., 250 trading days; configurable)
- For each day:
  - compute VaR using past window
  - compare to next-day realized P&L
  - mark breach
- Kupiec POF test:
  - compute p-value
  - include in metrics.json

### Outputs
- `reports/backtest.csv` with:
  - `date, var_hist, var_mc, pnl, breach_hist, breach_mc`
- `reports/metrics.json` includes:
  - breach rates
  - kupiec p-values
- Plot:
  - P&L and VaR thresholds overlay (or breaches highlighted)
- 1-page report in Spanish:
  - explain VaR, show backtest and breach rate interpretation

---

## 6) PDF Reporting (All Projects)
### 6.1 Requirements
- Must generate `reports/report.pdf` with **exactly 1 page**.
- Must be in **Spanish**, concise and executive-friendly.
- Must include:
  - Data range and data source line(s)
  - Method bullets (3–6)
  - Metrics table (small)
  - At least one chart (from `reports/figures/`)

### 6.2 Implementation options (choose one)
- Option A: LaTeX template compiled via `pdflatex` (preferred)
- Option B: Markdown → PDF via a tool (only if already available in repo environment)
- If using LaTeX:
  - Provide a minimal `.tex` template in `reports/template.tex`
  - Pipeline fills it (string substitution) and compiles

---

## 7) Work Plan (Execution Order)
Follow this order unless the repo already dictates otherwise:

1) Implement full scaffold for all 3 projects (folders, Makefiles, placeholders, tests).
2) FX VaR end-to-end first (fastest feedback).
3) CPI nowcast end-to-end.
4) Credit PD + ECL end-to-end.
5) Polish: tighten READMEs, ensure Spanish reports, ensure tests green.

---

## 8) Definition of Done (Portfolio-Level)
Each project folder must satisfy:
- `make install` succeeds
- `make lint` succeeds
- `make test` succeeds
- `make run` (or `python -m src.pipeline`) produces:
  - `reports/metrics.json`
  - `reports/figures/*.png`
  - `reports/report.pdf` (1 page, Spanish)
  - project-specific output table (`predictions.csv`, `ecl_sample.csv`, `backtest.csv`)
- README contains: problem, data, method, results, run steps, limitations, next steps.

---

## 9) Operating Instructions for You (Codex Agent)
When making changes:
1. Prefer small PR-sized commits (even locally).
2. Update or add tests alongside new functionality.
3. If you add a dependency, add it to requirements.txt and justify in README.
4. Never silently change schemas—document in README and update tests.
5. Keep pipelines robust: clear errors for missing files and mismatched columns.

**Deliverable expectation:** At the end, all three subprojects run cleanly and produce the required artifacts without manual steps.
