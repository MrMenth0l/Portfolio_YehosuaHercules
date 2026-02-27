"""Stage-4 baseline models for FX VaR."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_RANDOM_STATE, VAR_QUANTILE


def _validate_training_inputs(X_train: pd.DataFrame, y_train: pd.Series) -> None:
    if X_train.empty:
        raise ValueError("X_train is empty.")
    if y_train.empty:
        raise ValueError("y_train is empty.")
    if len(X_train) != len(y_train):
        raise ValueError("X_train and y_train lengths must match.")
    if X_train.isna().any().any():
        raise ValueError("X_train contains NaN values.")
    if y_train.isna().any():
        raise ValueError("y_train contains NaN values.")


def _validate_prediction_input(X: pd.DataFrame) -> None:
    if X.empty:
        raise ValueError("Prediction matrix is empty.")
    if X.isna().any().any():
        raise ValueError("Prediction matrix contains NaN values.")


def train_quantile_linear(X_train: pd.DataFrame, y_train: pd.Series) -> Any:
    """Train linear quantile baseline at q=1%."""
    _validate_training_inputs(X_train, y_train)
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                QuantileRegressor(
                    quantile=VAR_QUANTILE,
                    alpha=0.01,
                    solver="highs",
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    return model


def predict_quantile_linear(model: Any, X: pd.DataFrame) -> pd.Series:
    """Predict next-day 1% quantile PnL using linear quantile baseline."""
    _validate_prediction_input(X)
    predictions = pd.Series(model.predict(X), index=X.index, name="pred_qr_linear")
    return predictions


def train_quantile_tree(X_train: pd.DataFrame, y_train: pd.Series) -> Any:
    """Train tree-based quantile baseline at q=1%."""
    _validate_training_inputs(X_train, y_train)
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                GradientBoostingRegressor(
                    loss="quantile",
                    alpha=VAR_QUANTILE,
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=3,
                    min_samples_leaf=5,
                    random_state=MODEL_RANDOM_STATE,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    return model


def predict_quantile_tree(model: Any, X: pd.DataFrame) -> pd.Series:
    """Predict next-day 1% quantile PnL using tree quantile baseline."""
    _validate_prediction_input(X)
    predictions = pd.Series(model.predict(X), index=X.index, name="pred_qr_tree")
    return predictions


def train_linear_mean(X_train: pd.DataFrame, y_train: pd.Series) -> Any:
    """Train linear mean regression baseline."""
    _validate_training_inputs(X_train, y_train)
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )
    model.fit(X_train, y_train)
    return model


def predict_linear_mean(model: Any, X: pd.DataFrame) -> pd.Series:
    """Predict expected next-day PnL using linear mean baseline."""
    _validate_prediction_input(X)
    predictions = pd.Series(model.predict(X), index=X.index, name="pred_linear_mean")
    return predictions


def save_model(model: Any, path: Path) -> Path:
    """Save model artifact with joblib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: Path) -> Any:
    """Load model artifact saved with joblib."""
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at {path}.")
    return joblib.load(path)
