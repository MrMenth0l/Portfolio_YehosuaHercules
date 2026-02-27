"""Pipeline entrypoint for Stage 3 cleaning and feature engineering."""

from src.config import (
    DEFAULT_NOTIONAL_USD,
    FEATURE_LAGS,
    ensure_directories,
)
from src.features import TARGET_COLUMN, build_features, clean
from src.io import (
    download_data,
    load_feature_frame,
    load_raw,
    save_feature_frame,
    save_raw_snapshot,
)


def run() -> None:
    """Refresh raw data and persist Stage-3 feature frame."""
    ensure_directories()

    try:
        downloaded = download_data()
        raw_path = save_raw_snapshot(downloaded)
        raw_df = load_raw(raw_path)
        cleaned_df = clean(raw_df)
        features_df = build_features(cleaned_df)
        feature_path = save_feature_frame(features_df)
        loaded_features = load_feature_frame(feature_path)
    except Exception as exc:
        raise RuntimeError(
            "Stage 3 pipeline failed during data acquisition/feature engineering. "
            "Check network access to Banguat, strict raw schema (date, rate), "
            "and Stage-3 feature construction constraints."
        ) from exc

    min_date = loaded_features["date"].min().date().isoformat()
    max_date = loaded_features["date"].max().date().isoformat()
    lag_display = ",".join(str(lag) for lag in FEATURE_LAGS)

    print(
        "STAGE3_FEATURES "
        f"rows={len(loaded_features)} min_date={min_date} max_date={max_date} "
        f"notional_usd={DEFAULT_NOTIONAL_USD:.2f} lags={lag_display} "
        f"target={TARGET_COLUMN} feature_file={feature_path.name}"
    )
    print(
        "FX VaR Stage 3 cleaning and feature engineering complete. "
        "Modeling, backtesting, and reporting are not implemented yet."
    )


if __name__ == "__main__":
    run()
