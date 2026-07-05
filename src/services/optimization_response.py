"""Wrapper that packages an optimization result (or error) for callers.

Every call to the optimization service returns an ``OptimizationResponse``
rather than a raw ``Recommendation``. This gives callers a uniform object
to inspect: check ``status``, read the ``recommendation`` on success, or
read the ``message`` on failure — no exception handling required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.recommendation import Recommendation


@dataclass(frozen=True)
class OptimizationResponse:
    """Output of the optimization use case.

    Attributes:
        recommendation: The knapsack recommendation, or None on failure.
        status: "SUCCESS" or "FAILURE".
        timestamp: When the response was created.
        message: Error description on failure, None on success.
    """

    recommendation: Recommendation | None
    status: str
    timestamp: datetime
    message: str | None

    @classmethod
    def success(cls, recommendation: Recommendation) -> "OptimizationResponse":
        """Build a successful response wrapping the given recommendation.

        Args:
            recommendation: The optimization result to return.

        Returns:
            An OptimizationResponse with status "SUCCESS".
        """
        return cls(
            recommendation=recommendation,
            status="SUCCESS",
            timestamp=datetime.now(),
            message=None,
        )

    @classmethod
    def failure(cls, message: str) -> "OptimizationResponse":
        """Build a failure response with an error description.

        Args:
            message: Human-readable explanation of what went wrong.

        Returns:
            An OptimizationResponse with status "FAILURE" and no recommendation.
        """
        return cls(
            recommendation=None,
            status="FAILURE",
            timestamp=datetime.now(),
            message=message,
        )
