"""
ROLE: Abstract interface for persisting an optimization result to disk.

WHY THIS EXISTS:
    The CLI needs to save every run's input and solution somewhere, but the
    rest of the system should not need to know whether that "somewhere" is a
    folder of CSV files, a database, or a cloud bucket. This base class
    declares the one method any result-persistence strategy must provide, so
    a future format (e.g. Excel, JSON) is a new class, not a rewrite of the
    caller.

WHERE IMPLEMENTATIONS LIVE:
    Concrete writers live alongside this file in src/services/, e.g.
    csv_result_writer.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from services.optimization_response import OptimizationResponse


class BaseResultWriter(ABC):
    """
    This is an abstract base class (ABC) - a contract pattern, the mirror
    image of BaseDataLoader on the output side: it declares what a result
    writer must do without dictating how or in what file format. Any class
    that inherits from BaseResultWriter must provide a ``write()`` method, so
    callers can persist a run's results without caring whether they end up
    as CSV, JSON, or something else entirely.
    """

    @abstractmethod
    def write(self, request_id: str, response: OptimizationResponse, input_path: Path) -> Path:
        """Persist the response, alongside a copy of its input, to disk.

        Args:
            request_id: Identifier of the request that was solved.
            response: The result of solving that request.
            input_path: Path to the raw input file that was solved, so it can
                be copied alongside the result for reproducibility.

        Returns:
            The folder this run's files were written into.
        """
