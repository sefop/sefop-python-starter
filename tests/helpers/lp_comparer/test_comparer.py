"""Unit tests for the semantic LP model comparer."""

import textwrap
from pathlib import Path

from tests.helpers.lp_comparer.comparer import compare_lp


def _write_lp(tmp_path: Path, filename: str, content: str) -> Path:
    """Write *content* to *filename* inside *tmp_path* and return the path."""
    path = tmp_path / filename
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


_BASE_LP = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

_MINIMAL_LP_TEMPLATE = """\
    \\* {name} *\\

    max
    obj:
    +1 x

    s.t.

    bounds
       0 <= x <= 1
    binary
      x
    end
    """


# ---------------------------------------------------------------------------
# Identical models
# ---------------------------------------------------------------------------


def test__compare_lp__given_identical_files__returns_empty_list(tmp_path):
    # ARRANGE
    lp1 = _write_lp(tmp_path, "a.lp", _BASE_LP)
    lp2 = _write_lp(tmp_path, "b.lp", _BASE_LP)

    # ACT
    diffs = compare_lp(lp1, lp2)

    # ASSERT
    assert diffs == []


# ---------------------------------------------------------------------------
# Model-level differences
# ---------------------------------------------------------------------------


def test__compare_lp__given_name_differs__reports_model_modified(tmp_path):
    # ARRANGE
    lp1 = _write_lp(tmp_path, "a.lp", _MINIMAL_LP_TEMPLATE.format(name="model_a"))
    lp2 = _write_lp(tmp_path, "b.lp", _MINIMAL_LP_TEMPLATE.format(name="model_b"))

    # ACT
    diffs = compare_lp(lp1, lp2)

    # ASSERT
    model_diffs = [d for d in diffs if d.category == "model" and d.diff_type == "modified"]
    assert any("name" in d.detail.lower() for d in model_diffs)


def test__compare_lp__given_sense_differs__reports_model_modified(tmp_path):
    # ARRANGE
    lp1 = _write_lp(
        tmp_path,
        "a.lp",
        """\
        \\* m *\\

        max
        obj:
        +1 x

        s.t.

        bounds
           0 <= x <= 1
        binary
          x
        end
        """,
    )
    lp2 = _write_lp(
        tmp_path,
        "b.lp",
        """\
        \\* m *\\

        min
        obj:
        +1 x

        s.t.

        bounds
           0 <= x <= 1
        binary
          x
        end
        """,
    )

    # ACT
    diffs = compare_lp(lp1, lp2)

    # ASSERT
    sense_diffs = [d for d in diffs if d.category == "model" and "sense" in d.detail.lower()]
    assert len(sense_diffs) == 1
    assert sense_diffs[0].expected == "maximize"
    assert sense_diffs[0].actual == "minimize"


# ---------------------------------------------------------------------------
# Variable differences
# ---------------------------------------------------------------------------


def test__compare_lp__given_variable_missing_in_actual__reports_missing(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x

        s.t.

        c1:
        +1 x
        <= 100

        bounds
           0 <= x <= 1
        binary
          x
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    missing = [d for d in diffs if d.category == "variable" and d.diff_type == "missing"]
    assert any(d.name == "y" for d in missing)


def test__compare_lp__given_extra_variable_in_actual__reports_extra(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y
        +5 z

        s.t.

        c1:
        +1 x
        +2 y
        +1 z
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
           0 <= z <= 1
        binary
          x
          y
          z
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    extra = [d for d in diffs if d.category == "variable" and d.diff_type == "extra"]
    assert any(d.name == "z" for d in extra)


def test__compare_lp__given_variable_type_changed__reports_modified(tmp_path):
    # ARRANGE
    expected = _write_lp(
        tmp_path,
        "expected.lp",
        """\
        \\* model *\\

        max
        obj:
        +1 x

        s.t.

        bounds
           0 <= x <= 1
        binary
          x
        end
        """,
    )
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +1 x

        s.t.

        bounds
           0 <= x <= 10
        general
          x
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    type_diffs = [d for d in diffs if d.category == "variable" and d.diff_type == "modified"]
    assert any(d.name == "x" for d in type_diffs)


# ---------------------------------------------------------------------------
# Objective differences
# ---------------------------------------------------------------------------


def test__compare_lp__given_objective_coefficient_differs__reports_modified(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +99 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    obj_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
    assert len(obj_diffs) == 1
    assert obj_diffs[0].expected == 10.0
    assert obj_diffs[0].actual == 99.0


def test__compare_lp__given_variable_missing_from_objective__reports_missing(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    obj_missing = [d for d in diffs if d.category == "objective" and d.diff_type == "missing"]
    assert any("y" in d.detail for d in obj_missing)


def test__compare_lp__given_objective_missing_in_actual__reports_missing(tmp_path):
    # ARRANGE
    expected = _write_lp(
        tmp_path,
        "expected.lp",
        """\
        \\* model *\\

        max
        obj1:
        +10 x

        obj2:
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj1:
        +10 x

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    obj_missing = [d for d in diffs if d.category == "objective" and d.diff_type == "missing" and d.name == "obj2"]
    assert len(obj_missing) == 1


# ---------------------------------------------------------------------------
# Constraint differences
# ---------------------------------------------------------------------------


def test__compare_lp__given_constraint_missing_in_actual__reports_missing(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    missing = [d for d in diffs if d.category == "constraint" and d.diff_type == "missing"]
    assert any(d.name == "c1" for d in missing)


def test__compare_lp__given_extra_constraint_in_actual__reports_extra(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        c2:
        +1 x
        <= 5

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    extra = [d for d in diffs if d.category == "constraint" and d.diff_type == "extra"]
    assert any(d.name == "c2" for d in extra)


def test__compare_lp__given_constraint_sense_changed__reports_modified(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        >= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    sense_diffs = [
        d
        for d in diffs
        if d.category == "constraint" and d.diff_type == "modified" and d.name == "c1" and "sense" in d.detail.lower()
    ]
    assert len(sense_diffs) == 1
    assert sense_diffs[0].expected == "LTE"
    assert sense_diffs[0].actual == "GTE"


def test__compare_lp__given_constraint_rhs_changed__reports_modified(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 999

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    rhs_diffs = [
        d for d in diffs if d.category == "constraint" and d.diff_type == "modified" and "rhs" in d.detail.lower()
    ]
    assert len(rhs_diffs) == 1
    assert rhs_diffs[0].expected == 100.0
    assert rhs_diffs[0].actual == 999.0


def test__compare_lp__given_constraint_coefficient_differs__reports_modified(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c1:
        +5 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    coef_diffs = [
        d
        for d in diffs
        if d.category == "constraint" and d.diff_type == "modified" and "x" in d.detail and "c1" in d.detail
    ]
    assert len(coef_diffs) == 1
    assert coef_diffs[0].expected == 1.0
    assert coef_diffs[0].actual == 5.0


def test__compare_lp__given_variable_missing_from_constraint__reports_missing(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c1:
        +1 x
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    con_missing = [d for d in diffs if d.category == "constraint" and d.diff_type == "missing" and d.name == "c1"]
    assert any("y" in d.detail for d in con_missing)


# ---------------------------------------------------------------------------
# Tolerance
# ---------------------------------------------------------------------------


def test__compare_lp__given_coefficient_within_default_tolerance__reports_no_diff(tmp_path):
    # ARRANGE — coefficient of x is 10.0; write 10.0 + 1e-10, within the default 1e-9 tolerance
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10.0000000001 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    obj_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
    assert obj_diffs == []


def test__compare_lp__given_coefficient_outside_default_tolerance__reports_modified(tmp_path):
    # ARRANGE — coefficient of x is 10.0; write 11.0, outside the default 1e-9 tolerance
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +11 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual)

    # ASSERT
    obj_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
    assert len(obj_diffs) == 1


def test__compare_lp__given_custom_tolerance__is_applied_instead_of_default(tmp_path):
    # ARRANGE — coefficient of x is 10.0; write 10.5, within a custom tolerance=1.0
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(
        tmp_path,
        "actual.lp",
        """\
        \\* model *\\

        max
        obj:
        +10.5 x
        +20 y

        s.t.

        c1:
        +1 x
        +2 y
        <= 100

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(expected, actual, tolerance=1.0)

    # ASSERT
    obj_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
    assert obj_diffs == []


# ---------------------------------------------------------------------------
# Fail-fast behavior
# ---------------------------------------------------------------------------

# LP with several unrelated differences from _BASE_LP at once (sense, objective
# coefficient, and constraint RHS), used to confirm fail_fast stops at the
# first stage that finds anything rather than collecting every difference.
_LP_MANY_DIFFS = """\
    \\* model *\\

    min
    obj:
    +99 x

    s.t.

    c1:
    +5 x
    <= 999

    bounds
       0 <= x <= 1
    binary
      x
    end
    """


def test__compare_lp__given_fail_fast_true__returns_at_most_one_diff(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(tmp_path, "actual.lp", _LP_MANY_DIFFS)

    # ACT
    diffs = compare_lp(expected, actual, fail_fast=True)

    # ASSERT
    assert len(diffs) == 1


def test__compare_lp__given_fail_fast_false__returns_every_diff(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(tmp_path, "actual.lp", _LP_MANY_DIFFS)

    # ACT
    diffs = compare_lp(expected, actual, fail_fast=False)

    # ASSERT
    assert len(diffs) > 1


# Each of these LP variants isolates a single difference from _BASE_LP so the
# corresponding fail_fast test below can confirm the early-return fires in
# that specific stage (variable, objective, or constraint), not just anywhere.
_LP_MISSING_VAR = """\
    \\* model *\\

    max
    obj:
    +10 x

    s.t.

    c1:
    +1 x
    <= 100

    bounds
       0 <= x <= 1
    binary
      x
    end
    """

_LP_OBJ_COEF_DIFF = """\
    \\* model *\\

    max
    obj:
    +99 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

_LP_CON_RHS_DIFF = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 999

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """


def test__compare_lp__given_fail_fast_true_and_missing_variable__stops_at_variable_stage(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(tmp_path, "actual.lp", _LP_MISSING_VAR)

    # ACT
    diffs = compare_lp(expected, actual, fail_fast=True)

    # ASSERT
    assert len(diffs) == 1
    assert diffs[0].category == "variable"


def test__compare_lp__given_fail_fast_true_and_objective_coefficient_differs__stops_at_objective_stage(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(tmp_path, "actual.lp", _LP_OBJ_COEF_DIFF)

    # ACT
    diffs = compare_lp(expected, actual, fail_fast=True)

    # ASSERT
    assert len(diffs) == 1
    assert diffs[0].category == "objective"


def test__compare_lp__given_fail_fast_true_and_constraint_rhs_differs__stops_at_constraint_stage(tmp_path):
    # ARRANGE
    expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
    actual = _write_lp(tmp_path, "actual.lp", _LP_CON_RHS_DIFF)

    # ACT
    diffs = compare_lp(expected, actual, fail_fast=True)

    # ASSERT
    assert len(diffs) == 1
    assert diffs[0].category == "constraint"


# ---------------------------------------------------------------------------
# Order-agnostic comparison
# ---------------------------------------------------------------------------


def test__compare_lp__given_constraints_in_different_order__reports_no_diff(tmp_path):
    # ARRANGE — same constraints, different file order
    lp_a = _write_lp(
        tmp_path,
        "a.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c1:
        +1 x
        <= 50

        c2:
        +1 y
        <= 60

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )
    lp_b = _write_lp(
        tmp_path,
        "b.lp",
        """\
        \\* model *\\

        max
        obj:
        +10 x
        +20 y

        s.t.

        c2:
        +1 y
        <= 60

        c1:
        +1 x
        <= 50

        bounds
           0 <= x <= 1
           0 <= y <= 1
        binary
          x
          y
        end
        """,
    )

    # ACT
    diffs = compare_lp(lp_a, lp_b)

    # ASSERT
    assert diffs == []
