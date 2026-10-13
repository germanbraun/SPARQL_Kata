"""Compare a student's normalized result with the reference result.

SELECT results are compared as multisets (bags) of rows: row order is
ignored unless the kata sets order_sensitive, but duplicates DO count.
That way a missing DISTINCT is detected as a mistake.

The comparison reports *what* differs (missing rows, extra rows, columns,
order). Deciding *why* it differs is the job of hints.py.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .model import ResultSet, Row

# How student columns are matched to reference columns.
POSITIONAL = "positional"  # 1st column with 1st column, etc. Variable names don't matter.
BY_NAME = "by_name"        # match by variable name; column order doesn't matter.
COLUMN_MAPPINGS = (POSITIONAL, BY_NAME)

# Problem codes (the first problem found, in this order of checks).
PROBLEM_QUERY_TYPE = "query_type"      # e.g. student wrote ASK, kata expects SELECT
PROBLEM_ASK_ANSWER = "ask_answer"      # ASK returned the wrong boolean
PROBLEM_COLUMN_COUNT = "column_count"  # positional mapping, different number of columns
PROBLEM_COLUMN_NAMES = "column_names"  # by_name mapping, different variable names
PROBLEM_ROWS = "rows"                  # some rows missing and/or extra
PROBLEM_ORDER = "order"                # same rows, wrong order (order_sensitive only)


@dataclass
class Comparison:
    passed: bool
    problem: str | None = None
    reference_count: int = 0
    student_count: int = 0
    missing_rows: list[Row] = field(default_factory=list)  # in reference, not in student
    extra_rows: list[Row] = field(default_factory=list)    # in student, not in reference
    # True when every extra row also appears in the reference, i.e. the
    # student only has *repeated* copies of correct rows.
    extra_rows_are_duplicates: bool = False


def compare_results(
    reference: ResultSet,
    student: ResultSet,
    order_sensitive: bool = False,
    column_mapping: str = POSITIONAL,
) -> Comparison:
    if reference.query_type != student.query_type:
        return Comparison(passed=False, problem=PROBLEM_QUERY_TYPE)

    if reference.query_type == "ASK":
        same = reference.ask_answer == student.ask_answer
        return Comparison(passed=same, problem=None if same else PROBLEM_ASK_ANSWER)

    return _compare_select(reference, student, order_sensitive, column_mapping)


def _compare_select(
    reference: ResultSet,
    student: ResultSet,
    order_sensitive: bool,
    column_mapping: str,
) -> Comparison:
    counts = {"reference_count": len(reference.rows), "student_count": len(student.rows)}

    column_problem, student_rows = align_columns(reference, student, column_mapping)
    if column_problem:
        return Comparison(passed=False, problem=column_problem, **counts)

    reference_bag = Counter(reference.rows)
    student_bag = Counter(student_rows)

    # Counter subtraction keeps only positive counts:
    # a row expected twice but returned once appears once in `missing`.
    missing = sorted((reference_bag - student_bag).elements())
    extra = sorted((student_bag - reference_bag).elements())

    if missing or extra:
        extra_are_duplicates = bool(extra) and all(row in reference_bag for row in extra)
        return Comparison(
            passed=False,
            problem=PROBLEM_ROWS,
            missing_rows=missing,
            extra_rows=extra,
            extra_rows_are_duplicates=extra_are_duplicates,
            **counts,
        )

    if order_sensitive and reference.rows != student_rows:
        return Comparison(passed=False, problem=PROBLEM_ORDER, **counts)

    return Comparison(passed=True, **counts)


def align_columns(
    reference: ResultSet, student: ResultSet, column_mapping: str
) -> tuple[str | None, list[Row]]:
    """Return (problem, student_rows) with student columns in reference order.

    problem is None when the columns could be aligned.
    """
    if column_mapping == POSITIONAL:
        if len(student.variables) != len(reference.variables):
            return PROBLEM_COLUMN_COUNT, student.rows
        return None, student.rows

    if column_mapping == BY_NAME:
        if set(student.variables) != set(reference.variables):
            return PROBLEM_COLUMN_NAMES, student.rows
        # For each reference variable, where is it in the student's projection?
        positions = [student.variables.index(name) for name in reference.variables]
        reordered = [tuple(row[i] for i in positions) for row in student.rows]
        return None, reordered

    raise ValueError(f"Unknown column_mapping {column_mapping!r}, expected one of {COLUMN_MAPPINGS}")
