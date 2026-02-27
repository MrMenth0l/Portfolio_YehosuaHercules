"""Data acquisition and snapshot utilities for USD/GTQ rates."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from src.config import (
    BANGUAT_WSDL_ENDPOINT,
    DEFAULT_DOWNLOAD_END_DATE,
    DEFAULT_DOWNLOAD_START_DATE,
    DEFAULT_FEATURES_FILE,
    DEFAULT_PROCESSED_FILE,
    DEFAULT_RAW_FILE,
    RAW_METADATA_FILE,
    SOAP_BACKOFF_BASE_SECONDS,
    SOAP_BACKOFF_MAX_SECONDS,
    SOAP_MAX_RETRIES,
    SOAP_TIMEOUT_SECONDS,
)

REQUIRED_COLUMNS = ["date", "rate"]
FEATURE_REQUIRED_COLUMNS = ["date", "pnl_next_day"]
SOAP_ACTION = "http://www.banguat.gob.gt/variables/ws/TipoCambioRango"
SOAP_NAMESPACE = "http://www.banguat.gob.gt/variables/ws/"
SOAP_ENVELOPE_NAMESPACE = "http://schemas.xmlsoap.org/soap/envelope/"


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from exc


def _format_ddmmyyyy(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _iter_yearly_ranges(start: date, end: date) -> list[tuple[date, date]]:
    ranges: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        year_end = date(cursor.year, 12, 31)
        chunk_end = min(year_end, end)
        ranges.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return ranges


def _build_soap_envelope(start: date, end: date) -> bytes:
    envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <TipoCambioRango xmlns="{SOAP_NAMESPACE}">
      <fechainit>{_format_ddmmyyyy(start)}</fechainit>
      <fechafin>{_format_ddmmyyyy(end)}</fechafin>
    </TipoCambioRango>
  </soap:Body>
</soap:Envelope>
"""
    return envelope.encode("utf-8")


def _post_soap_request(start: date, end: date) -> bytes:
    request = urllib.request.Request(
        url=BANGUAT_WSDL_ENDPOINT,
        data=_build_soap_envelope(start, end),
        method="POST",
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{SOAP_ACTION}"',
        },
    )

    last_error: Exception | None = None
    for attempt in range(1, SOAP_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(
                request,
                timeout=SOAP_TIMEOUT_SECONDS,
            ) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt >= SOAP_MAX_RETRIES:
                raise RuntimeError(
                    "Banguat SOAP request failed after max retries. "
                    f"endpoint={BANGUAT_WSDL_ENDPOINT} range={start}:{end} "
                    f"attempts={SOAP_MAX_RETRIES} error={exc}"
                ) from exc

            delay_seconds = min(
                SOAP_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
                SOAP_BACKOFF_MAX_SECONDS,
            )
            time.sleep(delay_seconds)

    raise RuntimeError(
        "Banguat SOAP request failed unexpectedly without a captured exception."
    ) from last_error


def _extract_rows_from_payload(
    payload: bytes,
    start: date,
    end: date,
) -> list[dict[str, str | float]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise RuntimeError(
            "Invalid XML returned by Banguat SOAP endpoint "
            f"{BANGUAT_WSDL_ENDPOINT} for range {start} to {end}."
        ) from exc

    fault = root.find(f".//{{{SOAP_ENVELOPE_NAMESPACE}}}Fault")
    if fault is not None:
        fault_message = fault.findtext("faultstring") or "Unknown SOAP fault."
        raise RuntimeError(
            "Banguat SOAP fault from endpoint "
            f"{BANGUAT_WSDL_ENDPOINT} for range {start} to {end}: {fault_message}"
        )

    rows: list[dict[str, str | float]] = []
    for node in root.findall(f".//{{{SOAP_NAMESPACE}}}Var"):
        raw_date = node.findtext(f"{{{SOAP_NAMESPACE}}}fecha")
        raw_rate = node.findtext(f"{{{SOAP_NAMESPACE}}}venta")
        if raw_date is None or raw_rate is None:
            raise RuntimeError(
                "Banguat response row missing required fields 'fecha'/'venta' "
                f"for range {start} to {end}."
            )
        try:
            parsed_date = datetime.strptime(raw_date.strip(), "%d/%m/%Y").date()
        except ValueError as exc:
            raise RuntimeError(
                "Banguat returned non-parseable fecha "
                f"'{raw_date}' for range {start} to {end}."
            ) from exc
        try:
            parsed_rate = float(raw_rate.strip())
        except ValueError as exc:
            raise RuntimeError(
                "Banguat returned non-numeric venta "
                f"'{raw_rate}' for range {start} to {end}."
            ) from exc
        rows.append({"date": parsed_date.isoformat(), "rate": parsed_rate})

    return rows


def _validate_strict_schema(df: pd.DataFrame) -> None:
    if list(df.columns) != REQUIRED_COLUMNS:
        raise ValueError(
            "Strict schema required. Columns must be exactly in this order: date, rate."
        )


def _coerce_strict_types(df: pd.DataFrame) -> pd.DataFrame:
    try:
        converted = df.copy()
        converted["date"] = pd.to_datetime(converted["date"], errors="raise")
        converted["rate"] = pd.to_numeric(converted["rate"], errors="raise")
    except Exception as exc:
        raise ValueError(
            "Raw/processed data types are invalid. 'date' must be datetime-like and "
            "'rate' must be numeric."
        ) from exc
    return converted.sort_values("date").reset_index(drop=True)


def _compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_raw_metadata(csv_path: Path, df: pd.DataFrame) -> None:
    requested_start = str(
        df.attrs.get("requested_start_date", DEFAULT_DOWNLOAD_START_DATE)
    )
    requested_end = str(df.attrs.get("requested_end_date", DEFAULT_DOWNLOAD_END_DATE))

    min_date = df["date"].min().date().isoformat()
    max_date = df["date"].max().date().isoformat()

    metadata = {
        "source_name": "Banco de Guatemala (Banguat) TipoCambio SOAP",
        "source_endpoint": BANGUAT_WSDL_ENDPOINT,
        "soap_action": SOAP_ACTION,
        "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_start_date": requested_start,
        "requested_end_date": requested_end,
        "row_count": int(len(df)),
        "min_date": min_date,
        "max_date": max_date,
        "schema": REQUIRED_COLUMNS,
        "sha256": _compute_sha256(csv_path),
    }

    RAW_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    RAW_METADATA_FILE.write_text(
        f"{json.dumps(metadata, indent=2, sort_keys=True)}\n", encoding="utf-8"
    )


def download_data(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Download USD/GTQ data from Banguat SOAP and return a strict DataFrame."""
    start = _parse_iso_date(start_date or DEFAULT_DOWNLOAD_START_DATE, "start_date")
    end = _parse_iso_date(end_date or DEFAULT_DOWNLOAD_END_DATE, "end_date")

    if start > end:
        raise ValueError("start_date must be earlier than or equal to end_date.")

    all_rows: list[dict[str, str | float]] = []
    for chunk_start, chunk_end in _iter_yearly_ranges(start, end):
        payload = _post_soap_request(chunk_start, chunk_end)
        all_rows.extend(_extract_rows_from_payload(payload, chunk_start, chunk_end))

    if not all_rows:
        raise RuntimeError(
            "No FX rows were returned from Banguat for the requested range "
            f"{start.isoformat()} to {end.isoformat()}."
        )

    df = pd.DataFrame(all_rows, columns=REQUIRED_COLUMNS)
    df = _coerce_strict_types(df)
    df = df.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    df.attrs["requested_start_date"] = start.isoformat()
    df.attrs["requested_end_date"] = end.isoformat()
    return df


def save_raw_snapshot(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Save strict raw snapshot CSV and write metadata sidecar JSON."""
    _validate_strict_schema(df)
    out_path = path if path is not None else DEFAULT_RAW_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = _coerce_strict_types(df)
    normalized.attrs.update(df.attrs)

    csv_ready = normalized.copy()
    csv_ready["date"] = csv_ready["date"].dt.strftime("%Y-%m-%d")

    csv_ready.to_csv(out_path, index=False)
    _write_raw_metadata(out_path, normalized)
    return out_path


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """Load raw snapshot CSV with strict schema and dtype validation."""
    raw_path = path if path is not None else DEFAULT_RAW_FILE
    if not raw_path.exists():
        raise FileNotFoundError(
            "Raw data file not found at "
            f"{raw_path}. Expected file with strict columns: date, rate."
        )

    df = pd.read_csv(raw_path)
    _validate_strict_schema(df)
    return _coerce_strict_types(df)


def load_raw_fx_rates(path: Path | None = None) -> pd.DataFrame:
    """Backward-compatible alias for Stage-1 interface."""
    return load_raw(path)


def save_processed(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Persist strict processed dataset as Parquet."""
    _validate_strict_schema(df)
    out_path = path if path is not None else DEFAULT_PROCESSED_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = _coerce_strict_types(df)
    normalized.to_parquet(out_path, index=False)
    return out_path


def load_processed(path: Path | None = None) -> pd.DataFrame:
    """Load strict processed Parquet dataset."""
    processed_path = path if path is not None else DEFAULT_PROCESSED_FILE
    if not processed_path.exists():
        raise FileNotFoundError(
            "Processed data file not found at "
            f"{processed_path}. Expected Parquet file with columns: date, rate."
        )

    df = pd.read_parquet(processed_path)
    _validate_strict_schema(df)
    return _coerce_strict_types(df)


def _coerce_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in FEATURE_REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(
            "Feature frame schema mismatch. Missing required columns: "
            f"{missing_display}."
        )

    converted = df.copy()
    try:
        converted["date"] = pd.to_datetime(converted["date"], errors="raise")
        converted["pnl_next_day"] = pd.to_numeric(
            converted["pnl_next_day"],
            errors="raise",
        )
    except Exception as exc:
        raise ValueError(
            "Feature frame has invalid dtypes. 'date' must be datetime-like and "
            "'pnl_next_day' numeric."
        ) from exc

    converted = converted.sort_values("date").reset_index(drop=True)
    if converted.isna().any().any():
        raise ValueError("Feature frame contains NaNs.")
    if converted["date"].duplicated().any():
        raise ValueError("Feature frame must contain unique dates.")
    return converted


def save_feature_frame(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Persist Stage-3 feature frame as Parquet."""
    out_path = path if path is not None else DEFAULT_FEATURES_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = _coerce_feature_frame(df)
    normalized.to_parquet(out_path, index=False)
    return out_path


def load_feature_frame(path: Path | None = None) -> pd.DataFrame:
    """Load Stage-3 feature frame from Parquet."""
    feature_path = path if path is not None else DEFAULT_FEATURES_FILE
    if not feature_path.exists():
        raise FileNotFoundError(
            "Feature frame file not found at "
            f"{feature_path}. Expected a Stage-3 features parquet file."
        )

    df = pd.read_parquet(feature_path)
    return _coerce_feature_frame(df)
