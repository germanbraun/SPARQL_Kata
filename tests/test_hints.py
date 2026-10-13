from sparql_kata import hints
from sparql_kata.compare import compare_results
from sparql_kata.messages import hint_text
from sparql_kata.model import ResultSet


def select(rows, variables=("x",)):
    return ResultSet("SELECT", variables=list(variables), rows=rows)


def diagnose(reference, student, reference_ops=(), student_ops=()):
    comparison = compare_results(reference, student)
    return hints.diagnose(comparison, set(reference_ops), set(student_ops))


def test_missing_optional():
    reference = select([("a",), ("b",)])
    student = select([("a",)])
    assert diagnose(reference, student, {"LeftJoin"}, set()) == [hints.MISSING_OPTIONAL]


def test_missing_rows_without_optional_in_reference():
    assert diagnose(select([("a",), ("b",)]), select([("a",)])) == [hints.MISSING_ROWS]


def test_missing_distinct():
    reference = select([("a",), ("b",)])
    student = select([("a",), ("a",), ("b",)])
    assert diagnose(reference, student, {"Distinct"}, set()) == [hints.MISSING_DISTINCT]


def test_duplicate_rows_without_distinct_in_reference():
    assert diagnose(select([("a",)]), select([("a",), ("a",)])) == [hints.DUPLICATE_ROWS]


def test_join_explosion():
    reference = select([("a",), ("b",)])
    student = select([("a",), ("b",), ("c",), ("d",), ("e",), ("f",)])
    assert diagnose(reference, student) == [hints.JOIN_EXPLOSION]


def test_few_extra_rows():
    assert diagnose(select([("a",), ("b",)]), select([("a",), ("b",), ("c",)])) == [hints.EXTRA_ROWS]


def test_wrong_values_and_different_rows():
    assert diagnose(select([("a",), ("b",)]), select([("a",), ("z",)])) == [hints.WRONG_VALUES]
    assert diagnose(select([("a",), ("b",)]), select([("z",)])) == [hints.DIFFERENT_ROWS]


def test_passing_has_no_symptoms():
    assert diagnose(select([("a",)]), select([("a",)])) == []


def test_hint_text_override_and_fallback():
    overrides = {hints.MISSING_ROWS: {"es": "propio"}, hints.EXTRA_ROWS: "siempre"}
    assert hint_text(hints.MISSING_ROWS, "es", overrides) == "propio"
    assert hint_text(hints.MISSING_ROWS, "en", overrides).startswith("Some results")
    assert hint_text(hints.EXTRA_ROWS, "en", overrides) == "siempre"
    assert hint_text(hints.EXTRA_ROWS, "fr").startswith("You get")  # unknown lang -> English
