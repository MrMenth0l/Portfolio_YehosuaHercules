from pathlib import Path

import pandas as pd

import src.io as io
import src.pipeline as pipeline


def _sample_raw_df() -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "rate": [7.6, 7.7, 7.8],
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    df.attrs["requested_start_date"] = "1900-01-01"
    df.attrs["requested_end_date"] = "2026-02-22"
    return df


def _sample_feature_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "rate": [7.6, 7.7],
            "return_simple": [0.001, 0.0012],
            "return_log": [0.00099, 0.00119],
            "pnl": [10.0, 12.0],
            "pnl_next_day": [12.0, 11.0],
            "is_weekend": [0, 0],
        }
    )


def test_pipeline_always_refresh_calls_download_every_run(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    calls = {"download": 0}

    def fake_download() -> pd.DataFrame:
        calls["download"] += 1
        return _sample_raw_df()

    raw_path = tmp_path / "usd_gtq_daily.csv"
    feature_path = tmp_path / "features.parquet"

    monkeypatch.setattr(
        io,
        "RAW_METADATA_FILE",
        tmp_path / "usd_gtq_daily.metadata.json",
    )
    monkeypatch.setattr(pipeline, "ensure_directories", lambda: None)
    monkeypatch.setattr(pipeline, "download_data", fake_download)
    monkeypatch.setattr(
        pipeline,
        "save_raw_snapshot",
        lambda df: io.save_raw_snapshot(df, raw_path),
    )
    monkeypatch.setattr(
        pipeline,
        "load_raw",
        lambda path=None: io.load_raw(raw_path if path is None else path),
    )
    monkeypatch.setattr(pipeline, "clean", lambda df: df)
    monkeypatch.setattr(pipeline, "build_features", lambda df: _sample_feature_df())
    monkeypatch.setattr(
        pipeline,
        "save_feature_frame",
        lambda df: io.save_feature_frame(df, feature_path),
    )
    monkeypatch.setattr(
        pipeline,
        "load_feature_frame",
        lambda path=None: io.load_feature_frame(feature_path if path is None else path),
    )

    pipeline.run()
    pipeline.run()

    assert calls["download"] == 2
    assert "STAGE3_FEATURES" in capsys.readouterr().out


def test_pipeline_stage3_creates_features_parquet(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    raw_path = tmp_path / "usd_gtq_daily.csv"
    metadata_path = tmp_path / "usd_gtq_daily.metadata.json"
    feature_path = tmp_path / "features.parquet"

    monkeypatch.setattr(io, "RAW_METADATA_FILE", metadata_path)
    monkeypatch.setattr(pipeline, "ensure_directories", lambda: None)
    monkeypatch.setattr(pipeline, "download_data", _sample_raw_df)
    monkeypatch.setattr(
        pipeline,
        "save_raw_snapshot",
        lambda df: io.save_raw_snapshot(df, raw_path),
    )
    monkeypatch.setattr(
        pipeline,
        "load_raw",
        lambda path=None: io.load_raw(raw_path if path is None else path),
    )
    monkeypatch.setattr(pipeline, "clean", lambda df: df)
    monkeypatch.setattr(pipeline, "build_features", lambda df: _sample_feature_df())
    monkeypatch.setattr(
        pipeline,
        "save_feature_frame",
        lambda df: io.save_feature_frame(df, feature_path),
    )
    monkeypatch.setattr(
        pipeline,
        "load_feature_frame",
        lambda path=None: io.load_feature_frame(feature_path if path is None else path),
    )

    pipeline.run()

    output = capsys.readouterr().out
    assert "STAGE3_FEATURES" in output
    assert raw_path.exists()
    assert metadata_path.exists()
    assert feature_path.exists()
