"""Configuration values for the application.

All configuration lives here, in one place, rather than scattered as literal
strings across the codebase. A data scientist forking this repository to
point at their own data or output folder only needs to edit this one file.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    """Holds all configurable values for the application.

    Attributes:
        folder_path: Root directory where request subfolders live
            (data/1/data.json, data/2/data.json, …).
        solver_name: Solver technology passed to the MIP strategy.
        output_folder_path: Root directory each run's input and solution
            files are written under (output/1/<timestamp>/, …).
    """

    folder_path: str = "data"
    solver_name: str = "highs"
    output_folder_path: str = "output"
