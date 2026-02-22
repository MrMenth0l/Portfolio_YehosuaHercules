from pathlib import Path

import pandas as pd

import src.io as io
import src.pipeline as pipeline


def _sample_df() -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "rate": [7.6, 7.7],
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    df.attrs["requested_start_date"] = "1900-01-01"
    df.attrs["requested_end_date"] = "2026-02-22"
    return df


def test_pipeline_always_refresh_calls_download_every_run(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    calls = {"download": 0}

    def fake_download() -> pd.DataFrame:
        calls["download"] += 1
        return _sample_df()

    raw_path = tmp_path / "usd_gtq_daily.csv"
    processed_path = tmp_path / "fx_rates.parquet"

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
    monkeypatch.setattr(
        pipeline,
        "save_processed",
        lambda df: io.save_processed(df, processed_path),
    )
    monkeypatch.setattr(
        pipeline,
        "load_processed",
        lambda path=None: io.load_processed(processed_path if path is None else path),
    )
    monkeypatch.setattr(
        io,
        "RAW_METADATA_FILE",
        tmp_path / "usd_gtq_daily.metadata.json",
    )

    pipeline.run()
    pipeline.run()

    assert calls["download"] == 2
    assert "STAGE2_SNAPSHOT" in capsys.readouterr().out


def test_pipeline_creates_expected_files(monkeypatch, tmp_path: Path, capsys) -> None:
    raw_path = tmp_path / "usd_gtq_daily.csv"
    processed_path = tmp_path / "fx_rates.parquet"
    metadata_path = tmp_path / "usd_gtq_daily.metadata.json"

    monkeypatch.setattr(io, "RAW_METADATA_FILE", metadata_path)
    monkeypatch.setattr(pipeline, "ensure_directories", lambda: None)
    monkeypatch.setattr(pipeline, "download_data", _sample_df)
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
    monkeypatch.setattr(
        pipeline,
        "save_processed",
        lambda df: io.save_processed(df, processed_path),
    )
    monkeypatch.setattr(
        pipeline,
        "load_processed",
        lambda path=None: io.load_processed(processed_path if path is None else path),
    )

    pipeline.run()

    output = capsys.readouterr().out
    assert "STAGE2_SNAPSHOT" in output
    assert raw_path.exists()
    assert metadata_path.exists()
    assert processed_path.exists()
