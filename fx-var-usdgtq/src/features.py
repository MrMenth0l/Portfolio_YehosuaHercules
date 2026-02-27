"""Stage-3 cleaning and feature engineering for FX VaR."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DEFAULT_NOTIONAL_USD, DEFAULT_TEST_DAYS, FEATURE_LAGS

REQUIRED_INPUT_COLUMNS = ["date", "rate"]
TARGET_COLUMN = "pnl_next_day"


def _validate_input_columns(df: pd.DataFrame) -> None:
    if list(df.columns) != REQUIRED_INPUT_COLUMNS:
        raise ValueError(
            "build_features requires strict input columns in this order: date, rate."
        )


def _validate_lags(lags: tuple[int, ...]) -> tuple[int, ...]:
    if not lags:
        raise ValueError("At least one lag must be provided.")
    if any((not isinstance(lag, int)) or lag <= 0 for lag in lags):
        raise ValueError("All lags must be positive integers.")
    return tuple(sorted(set(lags)))


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw FX data by parsing types, sorting, and enforcing positive rates."""
    missing = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(f"Input data is missing required columns: {missing_display}.")

    cleaned = df[REQUIRED_INPUT_COLUMNS].copy()
    cleaned = cleaned.dropna(subset=["date", "rate"])

    try:
        cleaned["date"] = pd.to_datetime(cleaned["date"], errors="raise")
        cleaned["rate"] = pd.to_numeric(cleaned["rate"], errors="raise")
    except Exception as exc:
        raise ValueError(
            "Input data has invalid types. 'date' must be parseable and 'rate' numeric."
        ) from exc

    cleaned = cleaned.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    cleaned = cleaned.reset_index(drop=True)

    if cleaned.empty:
        raise ValueError("No rows remain after cleaning.")
    if (cleaned["rate"] <= 0).any():
        raise ValueError("All rates must be strictly positive for return calculations.")
    if not cleaned["date"].is_monotonic_increasing:
        raise ValueError("Dates must be sorted ascending after cleaning.")
    if cleaned["date"].duplicated().any():
        raise ValueError("Dates must be unique after cleaning.")

    return cleaned


def build_features(
    df: pd.DataFrame,
    notional_usd: float = DEFAULT_NOTIONAL_USD,
    lags: tuple[int, ...] = FEATURE_LAGS,
) -> pd.DataFrame:
    """Build deterministic, leakage-safe features and next-day PnL target."""
    _validate_input_columns(df)
    if notional_usd <= 0:
        raise ValueError("notional_usd must be strictly positive.")
    normalized_lags = _validate_lags(lags)

    features = clean(df)
    features["return_simple"] = features["rate"] / features["rate"].shift(1) - 1.0
    features["return_log"] = np.log(features["rate"] / features["rate"].shift(1))
    features["pnl"] = notional_usd * features["return_simple"]
    features["pnl_next_day"] = features["pnl"].shift(-1)
    features["is_weekend"] = (features["date"].dt.dayofweek >= 5).astype(int)

    for lag in normalized_lags:
        features[f"return_simple_lag_{lag}"] = features["return_simple"].shift(lag)
        features[f"return_log_lag_{lag}"] = features["return_log"].shift(lag)
        features[f"pnl_lag_{lag}"] = features["pnl"].shift(lag)
        features[f"roll_mean_return_simple_{lag}"] = (
            features["return_simple"].rolling(window=lag, min_periods=lag).mean()
        )
        features[f"roll_vol_return_simple_{lag}"] = (
            features["return_simple"].rolling(window=lag, min_periods=lag).std(ddof=0)
        )

    features = features.dropna().reset_index(drop=True)

    if features.empty:
        raise ValueError(
            "Insufficient rows after lag/rolling/target construction. "
            "Provide a longer history or smaller lag windows."
        )
    if features.isna().any().any():
        raise ValueError("Feature frame contains NaNs after cleanup.")
    if not features["date"].is_monotonic_increasing:
        raise ValueError("Feature dates must remain sorted ascending.")
    if features["date"].duplicated().any():
        raise ValueError("Feature dates must remain unique.")

    return features


def train_test_split_time(
    df: pd.DataFrame,
    test_days: int = DEFAULT_TEST_DAYS,
    target_col: str = TARGET_COLUMN,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split feature frame chronologically without leakage."""
    if target_col not in df.columns:
        raise ValueError(f"target_col '{target_col}' is not present in feature frame.")
    if test_days <= 0:
        raise ValueError("test_days must be a positive integer.")
    if "date" not in df.columns:
        raise ValueError("Feature frame must contain a 'date' column for time split.")
    if not df["date"].is_monotonic_increasing:
        raise ValueError("Feature frame must be sorted by date before time split.")
    if df["date"].duplicated().any():
        raise ValueError("Feature frame contains duplicate dates.")
    if len(df) <= test_days:
        raise ValueError(
            "Feature frame has "
            f"{len(df)} rows, which is not enough for test_days={test_days}."
        )

    split_idx = len(df) - test_days
    feature_cols = [col for col in df.columns if col != target_col]

    x_train = df.iloc[:split_idx][feature_cols].reset_index(drop=True)
    x_test = df.iloc[split_idx:][feature_cols].reset_index(drop=True)
    y_train = df.iloc[:split_idx][target_col].reset_index(drop=True)
    y_test = df.iloc[split_idx:][target_col].reset_index(drop=True)
    return x_train, x_test, y_train, y_test
