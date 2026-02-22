# GT-Quant Portfolio — Execution Guidelines & Outline (6-Week Sprint)
> Goal: Ship **3 “production-ish” quant projects** (Guatemala-flavored) with clean repos, tests, and **1-page PDFs**:
> 1) CPI nowcast, 2) Credit PD + mini IFRS-9 ECL, 3) FX VaR USD/GTQ.

---

## 0) Global Principles (Non-Negotiables)
### 0.1 Reproducibility
- Every repo must run end-to-end with **one command**:
  - `make install && make test && python -m src.pipeline` (or equivalent).
- Fixed random seeds everywhere.
- Data pipeline must be deterministic (same input snapshot ⇒ same output).

### 0.2 Separation of Concerns
- **Notebooks** = exploration only.
- All core logic lives in `src/` as importable functions.
- Notebooks call functions from `src/` (no duplicate logic).

### 0.3 Evidence Over Claims
- Every performance claim (MAPE, AUC, KS, VaR breaches, Kupiec p-value) must be:
  - computed in code,
  - saved to disk (e.g., `reports/metrics.json`),
  - shown in the 1-page PDF.

### 0.4 “Thin Vertical Slice” First
- Build the simplest working pipeline early:
  1) data ingest → 2) baseline model → 3) metrics → 4) plots → 5) 1-page PDF.
- Only then iterate improvements.

---

## 1) Standard Repo Template (Use for All 3 Projects)
### 1.1 Required Folder Structure
```
project/
  data/
    raw/              # raw snapshots (usually gitignored)
    processed/        # cleaned datasets (gitignored)
    external/         # optional: helper datasets (holidays, metadata)
    DATA_VERSION.md   # explains where raw snapshot came from + date
  notebooks/          # EDA only; no production logic
  src/
    __init__.py
    config.py         # paths, constants, parameters
    io.py             # download/load/save utilities
    features.py       # feature engineering
    model.py          # model training + prediction
    metrics.py        # evaluation metrics + tests
    plots.py          # plot generation functions
    pipeline.py       # main runnable script/module
  tests/
    test_io.py
    test_features.py
    test_metrics.py
    test_model_smoke.py
  reports/
    report.pdf        # 1-page executive report
    figures/          # exported charts used in report
    metrics.json      # saved evaluation outputs
  README.md
  requirements.txt
  Makefile
  pyproject.toml      # optional but recommended (ruff/black config)
```

### 1.2 Required Files (Exact Scope)
#### `README.md` must contain (in this order)
1. **Problem statement** (2–4 lines, non-technical).
2. **Why it matters** (risk/business use-case).
3. **Data**:
   - source(s),
   - frequency,
   - date range,
   - target variable definition,
   - data license/terms (if known).
4. **Method**:
   - baseline model,
   - features,
   - evaluation approach.
5. **Results**:
   - key metric numbers,
   - brief interpretation.
6. **How to run**:
   - setup,
   - command(s),
   - outputs produced.
7. **Repo structure** (short map).
8. **Limitations** + **Next steps** (bulleted).

#### `requirements.txt`
- Pin major libs if possible (optional exact versions).
- Must include:
  - `pandas`, `numpy`, `matplotlib`, `scipy`, `scikit-learn`, `statsmodels`,
  - `pytest`, `ruff`, `black`,
  - plus project-specific extras (xgboost/lightgbm for PD; etc.).

#### `Makefile` (minimum)
- `install`: install dependencies
- `lint`: ruff + black check
- `test`: pytest

#### `reports/report.pdf` (strict)
- **1 page** max.
- Visual-first: at least 1 chart.
- Must include:
  - a metric table (small),
  - data range,
  - methodology summary (3–6 bullets),
  - 2–3 actionable insights.

---

## 2) Stage Plan (Start-to-Finish Workflow)
You will repeat this workflow for each project.

### Stage 1 — Project Initialization (1–2 hours)
**Artifacts produced**
- Repo scaffold (folders + boilerplate files).
- `requirements.txt`, `Makefile`, empty `src/` modules, basic tests.

**Acceptance checklist**
- `pytest -q` runs (even if tests are placeholders).
- `ruff check .` and `black --check .` pass.
- `python -m src.pipeline` runs and prints a clear “not implemented” message.

---

### Stage 2 — Data Acquisition & Snapshotting (Half day)
**Artifacts produced**
- `src/io.py` with:
  - `download_data()` (if applicable),
  - `load_raw()`,
  - `save_raw_snapshot()`,
  - `load_processed()`,
  - `save_processed()`.
- `data/DATA_VERSION.md` with:
  - source URL/name,
  - retrieval date/time,
  - any filters,
  - notes about missing values or known quirks.

**Acceptance checklist**
- Raw snapshot saved locally under `data/raw/`.
- Loading raw snapshot produces a DataFrame with correct dtypes.
- Tests:
  - `test_io.py` verifies file existence + schema sanity.

---

### Stage 3 — Cleaning & Feature Pipeline (Half day)
**Artifacts produced**
- `src/features.py` with:
  - `clean(df)` (handles missing, date parsing, sorting),
  - `build_features(df)` (returns X, y aligned),
  - optional: `train_test_split_time(df)` for time series.
- `data/processed/` dataset created by pipeline.

**Acceptance checklist**
- No look-ahead leakage (time ordering preserved for time series).
- Features are reproducible and documented.
- Tests:
  - `test_features.py` checks:
    - no NaNs after feature build (or explicitly allowed ones),
    - output shapes,
    - date ordering.

---

### Stage 4 — Baseline Model (1 day)
**Artifacts produced**
- `src/model.py`:
  - `train(X_train, y_train)`,
  - `predict(model, X)`,
  - `save_model()` (optional; can store params instead),
  - `load_model()` (optional).
- `src/pipeline.py`:
  - runs end-to-end and writes outputs under `reports/`.

**Acceptance checklist**
- Baseline model trains without errors.
- Produces predictions for a defined test window.
- Tests:
  - `test_model_smoke.py` ensures:
    - training returns a model object,
    - predict returns correct length,
    - no NaNs in predictions.

---

### Stage 5 — Evaluation + Backtesting (1 day)
**Artifacts produced**
- `src/metrics.py`:
  - project-specific metrics (MAPE, AUC, KS, Kupiec, etc.)
  - `save_metrics(metrics_dict, path)`
- `reports/metrics.json` created by pipeline.
- Backtest routine implemented (rolling CV for CPI; holdout + calibration for PD; VaR backtest window for FX).

**Acceptance checklist**
- Metrics computed and persisted.
- Backtest logic matches real-world use:
  - CPI: rolling-origin evaluation
  - PD: proper train/valid/test split
  - VaR: daily VaR + breach counting

---

### Stage 6 — Plots + Report (1 day)
**Artifacts produced**
- `src/plots.py`:
  - functions to create and save PNG charts to `reports/figures/`.
- `reports/report.pdf` built from a template (LaTeX or markdown-to-pdf).
- At least:
  - 1 main performance plot,
  - 1 small table of metrics.

**Acceptance checklist**
- PDF is exactly 1 page.
- All numbers in PDF match `metrics.json`.
- Charts are readable (labels, axis, title).

---

### Stage 7 — Final Polish (0.5 day per repo)
**Artifacts produced**
- Clean README
- Clear error messages + CLI argument support (optional)
- “Limitations / Next Steps” added
- Repo badges (optional)
- Final tag/release (optional)

**Acceptance checklist**
- Fresh clone + setup yields same outputs.
- No “TODO” left in main path.
- Tests green.

---

## 3) Project A — CPI Nowcast (Guatemala)
### 3.1 Objective
Predict (nowcast) the CPI level or inflation rate for Guatemala for the most recent months.

### 3.2 Minimum Data Requirements
- Monthly CPI series (date, CPI value).
- Recommended extras:
  - month-of-year seasonality indicators,
  - holiday/calendar indicators (even simple month dummies is fine).

### 3.3 Core Implementation Scope
**Modules**
- `io.py`: load CPI series
- `features.py`:
  - ensure monthly frequency
  - create:
    - `month` dummy or sin/cos encoding
    - optional: lag features (if used)
- `model.py`:
  - SARIMAX baseline:
    - seasonal component (12 months)
    - exogenous calendar features (optional but recommended)
- `metrics.py`:
  - MAPE
- `pipeline.py`:
  - rolling-origin evaluation:
    - for each step, fit on history up to t, predict t+1
    - store predictions and errors

### 3.4 Required Evaluation Outputs
- Rolling predictions DataFrame:
  - columns: `date`, `y_true`, `y_pred`, `abs_pct_error`
- Metric:
  - `mape_last_12m`
- Plot:
  - actual vs predicted (last N months)
  - error over time (optional)

### 3.5 Definition of Done (CPI)
- Rolling backtest implemented.
- **MAPE ≤ 8%** on last-12-month rolling window (or document data/limitations honestly).
- 1-page PDF with:
  - plot actual vs predicted
  - MAPE number
  - data range + method bullets

---

## 4) Project B — Credit PD + Mini IFRS-9 ECL
### 4.1 Objective
Predict Probability of Default (PD) and compute a simplified Expected Credit Loss (ECL).

### 4.2 Minimum Data Requirements
A tabular loan dataset with:
- target: default / non-default label
- features: borrower and loan characteristics (income, loan amount, term, etc.)
- enough rows for split (thousands ideally)

### 4.3 Core Implementation Scope
**Modules**
- `features.py`:
  - cleaning:
    - missing value handling
    - categorical encoding (one-hot is fine)
  - train/valid/test split (no leakage)
- `model.py`:
  - baseline: logistic regression
  - improved: gradient boosting (XGBoost or LightGBM)
- `metrics.py`:
  - ROC-AUC
  - KS statistic
  - calibration curve (reliability)
- `pipeline.py`:
  - train baseline + boosted model
  - compare metrics
  - produce PD predictions on test set

### 4.4 Mini IFRS-9 ECL Demo Scope
You must produce a simple ECL calculation table.

**Definitions**
- PD: model predicted probability
- LGD: assume constant (e.g., 45%) or simple segment-based rule
- EAD: exposure (loan balance or original amount)

**ECL calculation**
- `ECL = PD × LGD × EAD`

**Staging logic (simple)**
- Stage 1: accounts “current” (or low delinquency) ⇒ 12-month PD proxy
- Stage 2: accounts “worse” (or higher delinquency) ⇒ lifetime PD proxy (you can scale PD up or use a longer horizon approximation)

**Artifacts required**
- `reports/ecl_sample.csv` (or table in PDF) showing:
  - account_id, PD, LGD, EAD, Stage, ECL
- PDF includes:
  - model metrics (AUC, KS)
  - calibration plot or bucket chart
  - ECL summary: total ECL and breakdown by stage

### 4.5 Definition of Done (Credit)
- ROC-AUC ≥ 0.75, KS ≥ 0.30
- Basic calibration plot included
- ECL demo computed and explained in PDF

---

## 5) Project C — FX VaR (USD/GTQ)
### 5.1 Objective
Estimate 1-day 99% Value-at-Risk for USD/GTQ changes and backtest it.

### 5.2 Minimum Data Requirements
- Daily USD/GTQ exchange rate history (close price).
- Enough history for backtest (≥ 2 years is good; less is possible but weaker).

### 5.3 Core Implementation Scope
**Modules**
- `features.py`:
  - compute returns:
    - log returns or simple % returns (pick one and stick to it)
  - compute P&L series for a defined position size (e.g., 1 USD notional or $10k notional)
- `model.py`:
  - Historical VaR:
    - VaR = 1% percentile of past P&L distribution (for 99% VaR)
  - Monte Carlo VaR:
    - assume returns ~ Normal(mean, std) OR bootstrap from history
    - simulate many next-day returns and compute VaR
- `metrics.py`:
  - breach counting
  - Kupiec test (POF)
- `pipeline.py`:
  - rolling backtest:
    - for each day t, compute VaR from window (e.g., last 250 days)
    - compare to realized P&L at t+1
    - record breach (1 if loss exceeds VaR threshold)

### 5.4 Required Evaluation Outputs
- Backtest table:
  - date, VaR_hist, VaR_mc, pnl_next_day, breach_hist, breach_mc
- Summary metrics:
  - breach_rate_hist, breach_rate_mc
  - Kupiec p-value for each method
- Plot:
  - P&L series with VaR thresholds overlaid (or breaches highlighted)

### 5.5 Definition of Done (FX VaR)
- 1-day 99% VaR computed via historical + MC
- Kupiec backtest reported (p-value)
- Breach commentary in PDF (what it means, whether too many/few breaches)

---

## 6) Cross-Project Quality Requirements (Final Product Checklist)
### 6.1 Code Quality
- `ruff` passes
- `black --check` passes
- clear function docstrings for public functions in `src/`

### 6.2 Tests (Minimum)
Each repo must have:
- `test_features.py`: shape + sanity checks
- `test_metrics.py`: known small examples (toy arrays) validating metric functions
- `test_model_smoke.py`: training and prediction smoke tests
- Target: **≥ 70% coverage for `src/`** (best-effort; do not fake coverage)

### 6.3 Outputs (Must Exist After Pipeline Run)
After running the pipeline:
- `reports/metrics.json`
- `reports/figures/*.png`
- `reports/report.pdf` (1 page)
- one “main output table”:
  - CPI: predictions table
  - PD: scored test set + ECL sample
  - VaR: backtest table

### 6.4 Report Content Requirements (All PDFs)
Each 1-page report must include:
- Title + date range
- Data source(s) line
- Method bullets (3–6 bullets)
- Metrics table (small)
- At least 1 chart
- 2–3 insights:
  - “what does this mean for a bank/risk team?”

---

## 7) Recommended Execution Order
If you want the smoothest start:
1) **FX VaR (Project C)** — easiest data + fast feedback loop
2) **CPI Nowcast (Project A)** — time series discipline
3) **Credit PD + ECL (Project B)** — most “bank-ish” + heaviest modeling

---

## 8) Final Deliverables Package (Portfolio-Level)
When all three repos are done, produce a “portfolio meta layer”:

### 8.1 Portfolio Index (Optional but strong)
- A top-level GitHub repo or page with:
  - links to the 3 repos
  - links to the 3 PDFs
  - 3 bullets per project: problem, method, result metric

### 8.2 CV + LinkedIn Snippet
- 1-page CV bullets that quantify results:
  - “CPI nowcast: SARIMAX baseline, rolling MAPE X%”
  - “Credit PD: AUC X, KS Y, ECL demo implemented”
  - “FX VaR: 1-day 99% VaR, Kupiec p-value Z, breach rate W%”

---

## 9) Immediate “Start Here” Checklist (Day 1)
1. Create the first repo (pick FX VaR or CPI).
2. Add the standard scaffold + Makefile + requirements.
3. Implement `src/pipeline.py` as a stub that creates the `reports/` folders.
4. Add `pytest` smoke tests that pass.
5. Start data snapshotting in `data/raw/` + document it in `DATA_VERSION.md`.

---

## 10) What “Done” Looks Like (Non-Technical Summary)
You will have 3 GitHub repos that:
- run end-to-end automatically,
- produce real metrics and plots,
- include tests,
- include a clean 1-page PDF report per project,
- and demonstrate you can build data → model → evaluation → reporting pipelines like a real risk/quant analyst.
