"""Feature engineering placeholders for Stage 1."""

import pandas as pd

_STAGE1_MSG = "Stage 1 scaffold only: feature engineering is not implemented yet."


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder feature builder for later implementation stages."""
    raise NotImplementedError(_STAGE1_MSG)
