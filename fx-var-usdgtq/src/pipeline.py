"""Pipeline entrypoint for Stage 4 baseline modeling."""

import pandas as pd

from src.config import (
    DEFAULT_TEST_DAYS,
    MODEL_DIR,
    PREDICTIONS_FILE,
    ensure_directories,
)
from src.features import TARGET_COLUMN, build_features, clean, train_test_split_time
from src.io import (
    download_data,
    load_feature_frame,
    load_raw,
    save_feature_frame,
    save_raw_snapshot,
)
from src.model import (
    predict_linear_mean,
    predict_quantile_linear,
    predict_quantile_tree,
    save_model,
    train_linear_mean,
    train_quantile_linear,
    train_quantile_tree,
)


def _build_model_matrix(df: pd.DataFrame) -> pd.DataFrame:
    matrix = df.select_dtypes(include=["number"]).copy()
    if matrix.empty:
        raise ValueError("No numeric feature columns available for model training.")
    if matrix.isna().any().any():
        raise ValueError("Model matrix contains NaN values.")
    return matrix


def _validate_prediction_series(
    name: str,
    predictions: pd.Series,
    expected_length: int,
) -> None:
    if len(predictions) != expected_length:
        raise ValueError(
            f"{name} prediction length {len(predictions)} does not match "
            f"expected test length {expected_length}."
        )
    if predictions.isna().any():
        raise ValueError(f"{name} predictions contain NaN values.")


def run() -> None:
    """Refresh data, build features, train Stage-4 models, and save predictions."""
    ensure_directories()
    try:
        downloaded = download_data()
        raw_path = save_raw_snapshot(downloaded)
        raw_df = load_raw(raw_path)
        cleaned_df = clean(raw_df)
        features_df = build_features(cleaned_df)
        feature_path = save_feature_frame(features_df)
        loaded_features = load_feature_frame(feature_path)

        x_train, x_test, y_train, y_test = train_test_split_time(
            loaded_features,
            test_days=DEFAULT_TEST_DAYS,
            target_col=TARGET_COLUMN,
        )
        x_train_matrix = _build_model_matrix(
            x_train.drop(columns=["date"], errors="ignore")
        )
        x_test_matrix = _build_model_matrix(
            x_test.drop(columns=["date"], errors="ignore")
        )

        model_qr_linear = train_quantile_linear(x_train_matrix, y_train)
        model_qr_tree = train_quantile_tree(x_train_matrix, y_train)
        model_linear_mean = train_linear_mean(x_train_matrix, y_train)

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        save_model(model_qr_linear, MODEL_DIR / "qr_linear_q01.joblib")
        save_model(model_qr_tree, MODEL_DIR / "qr_tree_q01.joblib")
        save_model(model_linear_mean, MODEL_DIR / "linear_mean.joblib")

        pred_qr_linear = predict_quantile_linear(model_qr_linear, x_test_matrix)
        pred_qr_tree = predict_quantile_tree(model_qr_tree, x_test_matrix)
        pred_linear_mean = predict_linear_mean(model_linear_mean, x_test_matrix)

        expected_len = len(y_test)
        _validate_prediction_series("pred_qr_linear", pred_qr_linear, expected_len)
        _validate_prediction_series("pred_qr_tree", pred_qr_tree, expected_len)
        _validate_prediction_series("pred_linear_mean", pred_linear_mean, expected_len)

        predictions = pd.DataFrame(
            {
                "date": pd.to_datetime(x_test["date"]).reset_index(drop=True),
                TARGET_COLUMN: y_test.reset_index(drop=True),
                "pred_qr_linear": pred_qr_linear.reset_index(drop=True),
                "pred_qr_tree": pred_qr_tree.reset_index(drop=True),
                "pred_linear_mean": pred_linear_mean.reset_index(drop=True),
            }
        )
        if predictions.isna().any().any():
            raise ValueError("Prediction table contains NaN values.")

        PREDICTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(PREDICTIONS_FILE, index=False)
    except Exception as exc:
        raise RuntimeError(
            "Stage 4 pipeline failed during data acquisition/modeling. "
            "Check network access to Banguat, strict raw schema (date, rate), "
            "Stage-4 feature matrix construction, and model training/prediction."
        ) from exc

    test_min_date = predictions["date"].min().date().isoformat()
    test_max_date = predictions["date"].max().date().isoformat()

    print(
        "STAGE4_MODELS "
        f"feature_rows={len(loaded_features)} test_rows={len(predictions)} "
        f"test_min_date={test_min_date} test_max_date={test_max_date} "
        f"target={TARGET_COLUMN} predictions_file={PREDICTIONS_FILE.name} "
        f"models=qr_linear_q01.joblib,qr_tree_q01.joblib,linear_mean.joblib"
    )
    print(
        "FX VaR Stage 4 baseline modeling complete. "
        "Modeling, backtesting, and reporting are not implemented yet."
    )


if __name__ == "__main__":
    run()
