"""Project paths and directory setup helpers."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

BANGUAT_WSDL_ENDPOINT = "https://banguat.gob.gt/variables/ws/TipoCambio.asmx"
DEFAULT_DOWNLOAD_START_DATE = "1900-01-01"
DEFAULT_DOWNLOAD_END_DATE = "2026-02-22"
SOAP_TIMEOUT_SECONDS = 30

DEFAULT_RAW_FILE = RAW_DIR / "usd_gtq_daily.csv"
RAW_METADATA_FILE = RAW_DIR / "usd_gtq_daily.metadata.json"
DEFAULT_PROCESSED_FILE = PROCESSED_DIR / "fx_rates.parquet"


def ensure_directories() -> None:
    """Create required project directories deterministically."""
    for path in (RAW_DIR, PROCESSED_DIR, EXTERNAL_DIR, REPORTS_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)
