from pathlib import Path

import pandas as pd

from src.model import (
    load_model,
    predict_linear_mean,
    predict_quantile_linear,
    predict_quantile_tree,
    save_model,
    train_linear_mean,
    train_quantile_linear,
    train_quantile_tree,
)


def _train_data() -> tuple[pd.DataFrame, pd.Series]:
    rows = 300
    frame = pd.DataFrame(
        {
            "f1": [0.001 * i for i in range(rows)],
            "f2": [0.002 * ((i % 7) + 1) for i in range(rows)],
            "f3": [0.0005 * ((i % 31) + 1) for i in range(rows)],
            "f4": [(-1) ** i * 0.001 for i in range(rows)],
        }
    )
    target = 0.5 * frame["f1"] - 0.3 * frame["f2"] + 0.2 * frame["f3"]
    return frame, target


def test_train_quantile_linear_returns_model_and_predictions() -> None:
    X, y = _train_data()
    model = train_quantile_linear(X, y)
    preds = predict_quantile_linear(model, X.tail(50))

    assert model is not None
    assert len(preds) == 50
    assert not preds.isna().any()


def test_train_quantile_tree_returns_model_and_predictions() -> None:
    X, y = _train_data()
    model = train_quantile_tree(X, y)
    preds = predict_quantile_tree(model, X.tail(50))

    assert model is not None
    assert len(preds) == 50
    assert not preds.isna().any()


def test_train_linear_mean_returns_model_and_predictions() -> None:
    X, y = _train_data()
    model = train_linear_mean(X, y)
    preds = predict_linear_mean(model, X.tail(50))

    assert model is not None
    assert len(preds) == 50
    assert not preds.isna().any()


def test_predict_outputs_match_length_and_have_no_nans() -> None:
    X, y = _train_data()
    X_test = X.tail(25)

    m1 = train_quantile_linear(X, y)
    m2 = train_quantile_tree(X, y)
    m3 = train_linear_mean(X, y)

    p1 = predict_quantile_linear(m1, X_test)
    p2 = predict_quantile_tree(m2, X_test)
    p3 = predict_linear_mean(m3, X_test)

    assert len(p1) == len(X_test)
    assert len(p2) == len(X_test)
    assert len(p3) == len(X_test)
    assert not p1.isna().any()
    assert not p2.isna().any()
    assert not p3.isna().any()


def test_save_load_model_roundtrip(tmp_path: Path) -> None:
    X, y = _train_data()
    model = train_linear_mean(X, y)
    model_path = tmp_path / "linear_mean.joblib"

    save_model(model, model_path)
    loaded_model = load_model(model_path)
    preds = predict_linear_mean(loaded_model, X.tail(10))

    assert model_path.exists()
    assert len(preds) == 10
    assert not preds.isna().any()
