"""Metrics helpers for Stage 1."""

import json
from pathlib import Path
from typing import Any


def save_metrics(metrics: dict[str, Any], out_path: Path) -> None:
    """Persist metrics as deterministic JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)
        f.write("\n")
