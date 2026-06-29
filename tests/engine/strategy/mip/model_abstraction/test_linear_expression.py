from engine.strategy.mip.optimization.model_abstraction.linear_expression import LinearExpression


def test__linear_expression__add__creates_term():
    # ARRANGE
    expr = LinearExpression()

    # ACT
    expr.add(0.12, "banana")

    # ASSERT
    assert expr.terms["banana"] == 0.12


def test__linear_expression__add__accumulates_same_variable():
    # ARRANGE
    expr = LinearExpression()
    expr.add(1.0, "banana")

    # ACT
    expr.add(2.0, "banana")

    # ASSERT
    assert expr.terms["banana"] == 3.0


def test__linear_expression__add__removes_term_when_cancelled():
    # ARRANGE
    expr = LinearExpression()
    expr.add(1.0, "banana")

    # ACT
    expr.add(-1.0, "banana")

    # ASSERT
    assert "banana" not in expr.terms


def test__linear_expression__terms__returns_copy():
    # ARRANGE
    expr = LinearExpression()
    expr.add(1.0, "banana")

    # ACT — mutating the returned dict must not affect the expression
    snapshot = expr.terms
    snapshot["banana"] = 999.0

    # ASSERT
    assert expr.terms["banana"] == 1.0
