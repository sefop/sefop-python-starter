from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_constraint import (
    ConstraintSign,
    LinearConstraint,
)
from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression


def test__linear_constraint__stores_fields_correctly():
    # ARRANGE
    expr = LinearExpression()
    expr.add(0.12, "banana")

    # ACT
    constraint = LinearConstraint(name="weight_limit", lhs=expr, sign=ConstraintSign.LEQ, rhs=5.0)

    # ASSERT
    assert constraint.name == "weight_limit"
    assert constraint.lhs is expr
    assert constraint.sign == ConstraintSign.LEQ
    assert constraint.rhs == 5.0
