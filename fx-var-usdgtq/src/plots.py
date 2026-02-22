"""Plotting placeholders for Stage 1."""

from pathlib import Path

import pandas as pd

_PLOT_MSG = "Stage 1 scaffold only: plot generation is not implemented yet."


def plot_backtest(backtest_df: pd.DataFrame, out_path: Path) -> None:
    """Placeholder plotting entrypoint."""
    raise NotImplementedError(_PLOT_MSG)
