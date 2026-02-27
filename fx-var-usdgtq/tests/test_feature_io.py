from pathlib import Path

import pandas as pd
import pytest

from src.io import load_feature_frame, save_feature_frame


def _feature_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-01-02", "2026-01-01"],
            "rate": [7.7, 7.6],
            "return_simple": [0.001, 0.0011],
            "return_log": [0.00099, 0.00109],
            "pnl": [10.0, 11.0],
            "pnl_next_day": [11.0, 12.0],
            "is_weekend": [0, 0],
        }
    )


def test_save_load_feature_frame_roundtrip(tmp_path: Path) -> None:
    output_path = tmp_path / "features.parquet"
    written_path = save_feature_frame(_feature_df(), output_path)
    reloaded = load_feature_frame(written_path)

    assert written_path.exists()
    assert len(reloaded) == 2
    assert reloaded["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]
    assert "pnl_next_day" in reloaded.columns


def test_save_feature_frame_requires_target_column(tmp_path: Path) -> None:
    bad_df = pd.DataFrame({"date": ["2026-01-01"], "pnl": [10.0]})

    with pytest.raises(ValueError):
        save_feature_frame(bad_df, tmp_path / "features.parquet")
