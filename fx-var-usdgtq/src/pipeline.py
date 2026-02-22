"""Pipeline entrypoint for Stage 2 data acquisition and snapshotting."""

from src.config import (
    DEFAULT_DOWNLOAD_END_DATE,
    DEFAULT_DOWNLOAD_START_DATE,
    ensure_directories,
)
from src.io import (
    download_data,
    load_processed,
    load_raw,
    save_processed,
    save_raw_snapshot,
)


def run() -> None:
    """Refresh raw data, persist processed snapshot, and print deterministic summary."""
    ensure_directories()

    try:
        downloaded = download_data()
        raw_path = save_raw_snapshot(downloaded)
        raw_df = load_raw(raw_path)
        processed_path = save_processed(raw_df)
        processed_df = load_processed(processed_path)
    except Exception as exc:
        raise RuntimeError(
            "Stage 2 pipeline failed during data acquisition/snapshotting. "
            "Check network access to Banguat, strict schema (date, rate), "
            "and file permissions."
        ) from exc

    min_date = processed_df["date"].min().date().isoformat()
    max_date = processed_df["date"].max().date().isoformat()
    requested_start = downloaded.attrs.get(
        "requested_start_date",
        DEFAULT_DOWNLOAD_START_DATE,
    )
    requested_end = downloaded.attrs.get(
        "requested_end_date",
        DEFAULT_DOWNLOAD_END_DATE,
    )

    print(
        "STAGE2_SNAPSHOT "
        f"rows={len(processed_df)} min_date={min_date} max_date={max_date} "
        f"requested_start={requested_start} requested_end={requested_end} "
        f"raw_file={raw_path.name} processed_file={processed_path.name}"
    )
    print(
        "FX VaR Stage 2 data acquisition complete. "
        "Modeling, backtesting, and reporting are not implemented yet."
    )


if __name__ == "__main__":
    run()
