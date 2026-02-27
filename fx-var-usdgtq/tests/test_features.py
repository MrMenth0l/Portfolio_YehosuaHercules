import pandas as pd
import pytest

from src.features import (
    TARGET_COLUMN,
    build_features,
    clean,
    train_test_split_time,
)


def _raw_df(rows: int = 700) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")
    rates = [7.2 + idx * 0.0005 for idx in range(rows)]
    return pd.DataFrame({"date": dates.astype(str), "rate": rates})


def test_clean_parses_and_sorts_dates() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-01", "2024-01-02"],
            "rate": ["7.5", "7.3", "7.4"],
        }
    )

    cleaned = clean(raw)

    assert list(cleaned.columns) == ["date", "rate"]
    assert cleaned["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
    ]
    assert cleaned["rate"].tolist() == [7.3, 7.4, 7.5]


def test_clean_rejects_missing_or_nonpositive_rate() -> None:
    missing_rate = pd.DataFrame({"date": ["2024-01-01"], "close": [7.5]})
    with pytest.raises(ValueError):
        clean(missing_rate)

    nonpositive = pd.DataFrame({"date": ["2024-01-01"], "rate": [0]})
    with pytest.raises(ValueError):
        clean(nonpositive)


def test_build_features_outputs_expected_columns() -> None:
    features = build_features(_raw_df())
    expected = {
        "date",
        "rate",
        "return_simple",
        "return_log",
        "pnl",
        "pnl_next_day",
        "is_weekend",
        "return_simple_lag_60",
        "return_log_lag_60",
        "pnl_lag_60",
        "roll_mean_return_simple_60",
        "roll_vol_return_simple_60",
    }

    assert expected.issubset(features.columns)
    assert set(features["is_weekend"].unique()).issubset({0, 1})


def test_build_features_has_no_nans_after_drop_policy() -> None:
    features = build_features(_raw_df())
    assert not features.isna().any().any()


def test_build_features_no_lookahead_target_alignment() -> None:
    features = build_features(_raw_df())
    lhs = features[TARGET_COLUMN].iloc[:-1].to_numpy()
    rhs = features["pnl"].iloc[1:].to_numpy()
    aligned = abs(lhs - rhs)
    assert (aligned < 1e-12).all()


def test_train_test_split_time_fixed_250_days() -> None:
    features = build_features(_raw_df())
    x_train, x_test, y_train, y_test = train_test_split_time(features, test_days=250)

    assert len(x_test) == 250
    assert len(y_test) == 250
    assert len(x_train) + len(x_test) == len(features)
    assert len(y_train) + len(y_test) == len(features)
    assert x_train["date"].max() < x_test["date"].min()


def test_train_test_split_time_insufficient_rows() -> None:
    features = build_features(_raw_df(rows=300))
    with pytest.raises(ValueError):
        train_test_split_time(features, test_days=250)
