from sparql_kata.compare import (
    BY_NAME, PROBLEM_ASK_ANSWER, PROBLEM_COLUMN_COUNT, PROBLEM_COLUMN_NAMES,
    PROBLEM_ORDER, PROBLEM_QUERY_TYPE, PROBLEM_ROWS, compare_results,
)
from sparql_kata.model import ResultSet


def select(variables, rows):
    return ResultSet("SELECT", variables=variables, rows=rows)


REFERENCE = select(["name", "email"], [('"Ana"', '"a@x"'), ('"Bruno"', "UNBOUND")])


def test_same_rows_in_other_order_pass():
    student = select(["n", "e"], list(reversed(REFERENCE.rows)))
    assert compare_results(REFERENCE, student).passed


def test_order_sensitive():
    student = select(["name", "email"], list(reversed(REFERENCE.rows)))
    result = compare_results(REFERENCE, student, order_sensitive=True)
    assert not result.passed and result.problem == PROBLEM_ORDER


def test_missing_rows():
    student = select(["name", "email"], [('"Ana"', '"a@x"')])
    result = compare_results(REFERENCE, student)
    assert result.problem == PROBLEM_ROWS
    assert result.missing_rows == [('"Bruno"', "UNBOUND")]
    assert result.extra_rows == []


def test_duplicates_count():
    student = select(["name", "email"], REFERENCE.rows + [('"Ana"', '"a@x"')])
    result = compare_results(REFERENCE, student)
    assert result.problem == PROBLEM_ROWS
    assert result.extra_rows == [('"Ana"', '"a@x"')]
    assert result.extra_rows_are_duplicates


def test_column_count():
    student = select(["name"], [('"Ana"',), ('"Bruno"',)])
    assert compare_results(REFERENCE, student).problem == PROBLEM_COLUMN_COUNT


def test_by_name_reorders_columns():
    student = select(["email", "name"], [('"a@x"', '"Ana"'), ("UNBOUND", '"Bruno"')])
    assert compare_results(REFERENCE, student, column_mapping=BY_NAME).passed


def test_by_name_wrong_names():
    student = select(["n", "e"], REFERENCE.rows)
    assert compare_results(REFERENCE, student, column_mapping=BY_NAME).problem == PROBLEM_COLUMN_NAMES


def test_ask():
    yes, no = ResultSet("ASK", ask_answer=True), ResultSet("ASK", ask_answer=False)
    assert compare_results(yes, yes).passed
    assert compare_results(yes, no).problem == PROBLEM_ASK_ANSWER


def test_query_type_mismatch():
    assert compare_results(REFERENCE, ResultSet("ASK", ask_answer=True)).problem == PROBLEM_QUERY_TYPE
