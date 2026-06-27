"""Command-line interface for the knapsack optimizer.

This is the delivery mechanism for the CLI. Its only job is to:
  1. Parse the command-line arguments (which request to solve).
  2. Delegate to the application layer via OptimizationService.
  3. Print a human-readable result.

Run with:
    python -m cli <request_id>

Example:
    python -m cli 1
"""
from __future__ import annotations

import argparse
import sys

from dependencies import create_optimization_service


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Solve a knapsack optimization request from a JSON data file."
    )
    parser.add_argument(
        "request_id",
        help="ID of the request to solve (must match a subfolder under the data/ directory).",
    )
    args = parser.parse_args()

    service = create_optimization_service()
    response = service.solve(args.request_id)

    if response.status == "SUCCESS":
        rec = response.recommendation
        print(f"\nStatus  : {response.status}")
        print("Products selected:")
        for product, qty in rec.quantities.items():
            print(
                f"  {product.name:<12} x{qty}"
                f"  ({product.calories * qty} cal,"
                f" ${product.price_usd * qty:.2f},"
                f" {product.weight_kg * qty:.2f} kg)"
            )
        print(f"Total calories : {rec.total_calories}")
        print(f"Total cost     : ${rec.total_cost_usd:.2f}")
        print(f"Total weight   : {rec.total_weight_kg:.2f} kg")
        sys.exit(0)
    else:
        print(f"\nStatus  : {response.status}")
        print(f"Reason  : {response.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
