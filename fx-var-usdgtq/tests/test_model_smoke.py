import pandas as pd
import pytest

from src.model import predict_var, train_var_model


def test_train_var_model_stage1_placeholder() -> None:
    features = pd.DataFrame({"return": [0.01, -0.02, 0.005]})

    with pytest.raises(NotImplementedError) as exc_info:
        train_var_model(features)

    assert "Stage 1 scaffold" in str(exc_info.value)


def test_predict_var_stage1_placeholder() -> None:
    features = pd.DataFrame({"return": [0.01, -0.02, 0.005]})

    with pytest.raises(NotImplementedError) as exc_info:
        predict_var(model=None, features=features)

    assert "Stage 1 scaffold" in str(exc_info.value)
