"""Command-line interface for the knapsack optimizer.

This is the delivery mechanism for the CLI. Its only job is to:
  1. Parse the command-line arguments (which request to solve).
  2. Delegate to the application layer via OptimizationService.
  3. Persist the result to disk via a BaseResultWriter and report where.

Run with:
    python -m cli <request_id>

Example:
    python -m cli 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from services.optimization_service import OptimizationService
from services.json_data_loader import JsonDataLoader
from services.csv_result_writer import CsvResultWriter
from services.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a knapsack optimization request given some data")
    parser.add_argument(
        "request_id",
        help="ID of the request to solve (must match a subfolder under the data/ directory).",
    )
    parser.add_argument(
        "--data-folder",
        default=None,
        help="Override the folder containing request subfolders (default: Settings().folder_path).",
    )
    parser.add_argument(
        "--output-folder",
        default=None,
        help="Override the folder solutions are written to (default: Settings().output_folder_path).",
    )
    args = parser.parse_args()

    settings = Settings()
    # Command-line flags win over Settings so callers (including tests) can
    # point at an arbitrary data/output location without editing Settings or
    # changing the working directory.
    data_folder = args.data_folder or settings.folder_path
    output_folder = args.output_folder or settings.output_folder_path
    loader = JsonDataLoader(folder_path=data_folder)
    writer = CsvResultWriter(output_folder_path=output_folder)
    service = OptimizationService(request_loader=loader)
    response = service.solve(args.request_id)

    # The writer only knows how to copy a file, not where JsonDataLoader's
    # "{folder}/{request_id}/data.json" convention lives, so that path is
    # built here rather than inside the writer.
    input_path = Path(data_folder) / args.request_id / "data.json"
    run_folder = writer.write(args.request_id, response, input_path)
    print(f"Results written to {run_folder}")

    sys.exit(0 if response.recommendation is not None else 1)


if __name__ == "__main__":
    main()
