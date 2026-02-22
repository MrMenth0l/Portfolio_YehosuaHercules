import json
from pathlib import Path

from src.metrics import save_metrics


def test_save_metrics_writes_deterministic_json(tmp_path: Path) -> None:
    out_path = tmp_path / "nested" / "metrics.json"
    payload = {"z_metric": 2, "a_metric": 1}

    save_metrics(payload, out_path)

    assert out_path.exists()
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert loaded == payload

    text = out_path.read_text(encoding="utf-8")
    assert text.index('"a_metric"') < text.index('"z_metric"')
