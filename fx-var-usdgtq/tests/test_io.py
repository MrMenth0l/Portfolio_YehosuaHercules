from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd
import pytest

import src.io as io


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> bool:
        return False


def _soap_response_xml(rows: list[tuple[str, str, str]]) -> bytes:
    vars_xml = "".join(
        (
            "<Var>"
            f"<fecha>{fecha}</fecha>"
            f"<venta>{venta}</venta>"
            f"<compra>{compra}</compra>"
            "</Var>"
        )
        for fecha, venta, compra in rows
    )
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soap:Body>"
        '<TipoCambioRangoResponse xmlns="http://www.banguat.gob.gt/variables/ws/">'
        f"<TipoCambioRangoResult><Vars>{vars_xml}</Vars></TipoCambioRangoResult>"
        "</TipoCambioRangoResponse>"
        "</soap:Body>"
        "</soap:Envelope>"
    )
    return xml.encode("utf-8")


def _soap_fault_xml(message: str) -> bytes:
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soap:Body>"
        "<soap:Fault>"
        "<faultcode>soap:Server</faultcode>"
        f"<faultstring>{message}</faultstring>"
        "</soap:Fault>"
        "</soap:Body>"
        "</soap:Envelope>"
    )
    return xml.encode("utf-8")


def test_load_raw_missing_file_has_actionable_message(tmp_path: Path) -> None:
    missing_path = tmp_path / "usd_gtq_daily.csv"

    with pytest.raises(FileNotFoundError) as exc_info:
        io.load_raw(missing_path)

    message = str(exc_info.value)
    assert "usd_gtq_daily.csv" in message
    assert "date" in message
    assert "rate" in message


def test_download_data_parses_banguat_xml(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _soap_response_xml(
        [
            ("01/01/2026", "7.66451", "7.60000"),
            ("02/01/2026", "7.66536", "7.60000"),
        ]
    )

    def fake_urlopen(request: urllib.request.Request, timeout: int) -> _FakeResponse:
        assert "TipoCambioRango" in request.data.decode("utf-8")
        return _FakeResponse(payload)

    monkeypatch.setattr(io.urllib.request, "urlopen", fake_urlopen)
    df = io.download_data("2026-01-01", "2026-01-02")

    assert list(df.columns) == ["date", "rate"]
    assert len(df) == 2
    assert df["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-01-01", "2026-01-02"]
    assert df["rate"].tolist() == [7.66451, 7.66536]
    assert df.attrs["requested_start_date"] == "2026-01-01"
    assert df.attrs["requested_end_date"] == "2026-01-02"


def test_download_data_chunks_and_combines_ranges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = [
        _soap_response_xml(
            [
                ("31/12/2025", "7.70000", "7.60000"),
                ("01/01/2026", "7.50000", "7.60000"),
            ]
        ),
        _soap_response_xml(
            [
                ("01/01/2026", "7.80000", "7.60000"),
                ("02/01/2026", "7.90000", "7.60000"),
            ]
        ),
    ]

    call_count = {"count": 0}

    def fake_urlopen(_: urllib.request.Request, timeout: int) -> _FakeResponse:
        call_count["count"] += 1
        return _FakeResponse(payloads.pop(0))

    monkeypatch.setattr(io.urllib.request, "urlopen", fake_urlopen)
    df = io.download_data("2025-12-31", "2026-01-02")

    assert call_count["count"] == 2
    assert df["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2025-12-31",
        "2026-01-01",
        "2026-01-02",
    ]
    assert df["rate"].tolist() == [7.7, 7.8, 7.9]


def test_download_data_soap_fault_raises_actionable_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _soap_fault_xml("Server was unable to process request.")

    def fake_urlopen(_: urllib.request.Request, timeout: int) -> _FakeResponse:
        return _FakeResponse(payload)

    monkeypatch.setattr(io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError) as exc_info:
        io.download_data("2026-01-01", "2026-01-10")

    message = str(exc_info.value)
    assert io.BANGUAT_WSDL_ENDPOINT in message
    assert "2026-01-01" in message
    assert "2026-01-10" in message


def test_save_raw_snapshot_enforces_strict_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad_df = pd.DataFrame({"date": ["2026-01-01"], "rate": [7.6], "extra": [1]})
    with pytest.raises(ValueError):
        io.save_raw_snapshot(bad_df, tmp_path / "bad.csv")

    metadata_path = tmp_path / "usd_gtq_daily.metadata.json"
    monkeypatch.setattr(io, "RAW_METADATA_FILE", metadata_path)

    good_df = pd.DataFrame({"date": ["2026-01-01"], "rate": [7.6]})
    output_path = io.save_raw_snapshot(good_df, tmp_path / "usd_gtq_daily.csv")

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").splitlines()[0] == "date,rate"
    assert metadata_path.exists()


def test_load_raw_strict_schema_and_dtypes(tmp_path: Path) -> None:
    bad_schema_path = tmp_path / "bad.csv"
    bad_schema_path.write_text("date,rate,extra\n2026-01-01,7.6,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        io.load_raw(bad_schema_path)

    good_path = tmp_path / "good.csv"
    good_path.write_text(
        "date,rate\n2026-01-02,7.7\n2026-01-01,7.6\n",
        encoding="utf-8",
    )
    loaded = io.load_raw(good_path)

    assert list(loaded.columns) == ["date", "rate"]
    assert loaded["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]
    assert loaded["rate"].tolist() == [7.6, 7.7]
