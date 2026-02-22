import pandas as pd
import pytest

from src.features import build_features


def test_build_features_is_stage1_placeholder() -> None:
    df = pd.DataFrame({"date": ["2024-01-01"], "rate": [7.8]})

    with pytest.raises(NotImplementedError) as exc_info:
        build_features(df)

    assert "Stage 1 scaffold" in str(exc_info.value)
