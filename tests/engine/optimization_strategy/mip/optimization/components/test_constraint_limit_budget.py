import pytest
from domain.product import Product
from domain.request import Request
from engine.optimization.mip.optimization.components.constraint_limit_budget import ConstraintLimitBudget
from engine.optimization.mip.optimization.model_abstraction.linear_constraint import ConstraintSign, LinearConstraint
from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from engine.optimization.mip.optimization.optimization import Optimization


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__constraint_limit_budget__matches_expected_constraint(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])
    expected_lhs = LinearExpression()
    expected_lhs.add(banana.price_usd, Optimization.variable_name(banana.name))
    expected_lhs.add(chips.price_usd, Optimization.variable_name(chips.name))
    expected = LinearConstraint(
        name="budget_limit", lhs=expected_lhs, sign=ConstraintSign.LEQ, rhs=request.max_budget_usd
    )

    # ACT
    constraint = ConstraintLimitBudget().build(request, name_fn=Optimization.variable_name)

    # ASSERT — compared field-by-field, not with `==` on the whole object,
    # so float fields (rhs, term coefficients) go through pytest.approx
    # rather than exact equality.
    assert constraint.name == expected.name
    assert constraint.sign == expected.sign
    assert constraint.rhs == pytest.approx(expected.rhs)
    assert constraint.lhs.terms == pytest.approx(expected.lhs.terms)
