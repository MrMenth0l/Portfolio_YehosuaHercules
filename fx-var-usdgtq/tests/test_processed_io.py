from pathlib import Path

import pandas as pd
import pytest

from src.io import load_processed, save_processed


def test_save_load_processed_parquet_roundtrip(tmp_path: Path) -> None:
    input_df = pd.DataFrame(
        {
            "date": ["2026-01-02", "2026-01-01"],
            "rate": [7.7, 7.6],
        }
    )
    output_path = tmp_path / "fx_rates.parquet"

    written_path = save_processed(input_df, output_path)
    reloaded = load_processed(written_path)

    assert written_path.exists()
    assert list(reloaded.columns) == ["date", "rate"]
    assert reloaded["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]
    assert reloaded["rate"].tolist() == [7.6, 7.7]


def test_save_processed_enforces_strict_schema(tmp_path: Path) -> None:
    bad_df = pd.DataFrame({"date": ["2026-01-01"], "rate": [7.6], "extra": [1]})

    with pytest.raises(ValueError):
        save_processed(bad_df, tmp_path / "bad.parquet")
