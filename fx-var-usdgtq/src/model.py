"""Modeling placeholders for Stage 1."""

from typing import Any

import pandas as pd

_TRAIN_MSG = "Stage 1 scaffold only: model training is not implemented yet."
_PREDICT_MSG = "Stage 1 scaffold only: prediction is not implemented yet."


def train_var_model(features: pd.DataFrame) -> Any:
    """Placeholder model training entrypoint."""
    raise NotImplementedError(_TRAIN_MSG)


def predict_var(model: Any, features: pd.DataFrame) -> pd.Series:
    """Placeholder prediction entrypoint."""
    raise NotImplementedError(_PREDICT_MSG)
