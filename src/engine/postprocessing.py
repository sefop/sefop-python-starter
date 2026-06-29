"""Post-processing stage that refines optimizer results.

This module sits at the end of the optimization pipeline. The default
implementation is intentionally a pass-through — override it to add
solution validation, result enrichment, or reporting without touching
the optimizer itself.
"""

from domain.recommendation import Recommendation


class PostProcess:
    """Post-processing step after strategy execution.

    Override this class to add custom post-processing logic such as
    solution validation, result enrichment, or reporting.
    """

    def run(self, recommendation: Recommendation) -> Recommendation:
        """Apply post-processing to the recommendation.

        Default implementation returns the recommendation unchanged.
        """
        return recommendation
