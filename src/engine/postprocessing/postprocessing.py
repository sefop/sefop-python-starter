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
        """Sort selected products from highest to lowest quantity.

        The solver returns products in an arbitrary order. Sorting by quantity
        makes the output deterministic and easier to read — the product you
        picked the most of appears first.
        """
        sorted_quantities = dict(sorted(recommendation.quantities.items(), key=lambda item: item[1], reverse=True))
        return Recommendation(request=recommendation.request, quantities=sorted_quantities)
