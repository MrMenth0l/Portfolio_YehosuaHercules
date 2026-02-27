from pathlib import Path

import pandas as pd

import src.io as io
import src.pipeline as pipeline


def _sample_raw_df(rows: int = 700) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")
    rates = [7.2 + idx * 0.0005 for idx in range(rows)]
    df = pd.DataFrame({"date": dates, "rate": rates})
    df.attrs["requested_start_date"] = "1900-01-01"
    df.attrs["requested_end_date"] = "2026-02-22"
    return df


def _patch_stage4_paths(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path]:
    raw_path = tmp_path / "usd_gtq_daily.csv"
    metadata_path = tmp_path / "usd_gtq_daily.metadata.json"
    predictions_path = tmp_path / "reports" / "fx-var_usdgtq_predictions.csv"
    model_dir = tmp_path / "models"

    monkeypatch.setattr(io, "RAW_METADATA_FILE", metadata_path)
    monkeypatch.setattr(pipeline, "MODEL_DIR", model_dir)
    monkeypatch.setattr(pipeline, "PREDICTIONS_FILE", predictions_path)
    return raw_path, metadata_path, predictions_path


def test_pipeline_stage4_writes_predictions_csv_with_required_columns(
    monkeypatch,
    tmp_path: Path,
) -> None:
    raw_path, _, predictions_path = _patch_stage4_paths(monkeypatch, tmp_path)

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

    pipeline.run()

    output = pd.read_csv(predictions_path)
    assert list(output.columns) == [
        "date",
        "pnl_next_day",
        "pred_qr_linear",
        "pred_qr_tree",
        "pred_linear_mean",
    ]
    assert len(output) == 250
    assert not output.isna().any().any()


def test_pipeline_stage4_saves_all_model_files(monkeypatch, tmp_path: Path) -> None:
    raw_path, _, _ = _patch_stage4_paths(monkeypatch, tmp_path)
    model_dir = tmp_path / "models"

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

    pipeline.run()

    assert (model_dir / "qr_linear_q01.joblib").exists()
    assert (model_dir / "qr_tree_q01.joblib").exists()
    assert (model_dir / "linear_mean.joblib").exists()


def test_pipeline_stage4_uses_fixed_250_day_test_window(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    raw_path, _, predictions_path = _patch_stage4_paths(monkeypatch, tmp_path)

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

    pipeline.run()

    output = pd.read_csv(predictions_path)
    stdout = capsys.readouterr().out
    assert len(output) == 250
    assert "STAGE4_MODELS" in stdout
