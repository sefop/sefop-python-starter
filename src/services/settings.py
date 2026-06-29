"""Configuration values for the application.

Configuration comes from the external environment (env vars, defaults).
The rest of the application never reads environment variables directly — it
reads from Settings instead, so configuration is centralized and easy to change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Holds all configurable values for the application.

    Each field reads from an environment variable first, falling back to a
    sensible default. This means data scientists can point the CLI at a
    different data folder without touching the code:

        SEFOP_FOLDER_PATH=my_data python -m cli 1
    """

    # Root directory where request subfolders live (data/1/data.json, data/2/data.json, …)
    folder_path: str = field(
        default_factory=lambda: os.environ.get("SEFOP_FOLDER_PATH", "data")
    )
    # Solver technology passed to the MIP strategy
    solver_name: str = field(
        default_factory=lambda: os.environ.get("SEFOP_SOLVER_NAME", "highs")
    )
