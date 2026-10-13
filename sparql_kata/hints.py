"""Diagnose *why* a student's result differs, as a list of symptom codes.

Input:
  - the Comparison (what differs: missing rows, extra rows, ...)
  - the algebra operators used by the reference and the student query,
    e.g. {"SelectQuery", "Project", "BGP", "LeftJoin", "Distinct"}.
    "LeftJoin" is how SPARQL algebra represents OPTIONAL.

Output: symptom codes (constants below). The text shown to students lives
in messages.py, so wording can change without touching this logic.

The rules are intentionally simple if/else checks, one symptom per case,
so it's easy to see why a given hint was chosen. Add new rules here.
"""

from __future__ import annotations

from .compare import (
    PROBLEM_ASK_ANSWER,
    PROBLEM_COLUMN_COUNT,
    PROBLEM_COLUMN_NAMES,
    PROBLEM_ORDER,
    PROBLEM_QUERY_TYPE,
    Comparison,
)

# --- Symptom codes -----------------------------------------------------------
# Detected by the grader, not by diagnose():
QUERY_ERROR = "query_error"              # student query failed to parse/run
FORBIDDEN_FEATURE = "forbidden_feature"  # e.g. SERVICE
OVERFITTED = "overfitted"                # passes visible dataset, fails a hidden one

# Detected by diagnose():
WRONG_QUERY_TYPE = "wrong_query_type"
WRONG_ASK_ANSWER = "wrong_ask_answer"
WRONG_COLUMNS = "wrong_columns"
WRONG_ORDER = "wrong_order"
MISSING_DISTINCT = "missing_distinct"
DUPLICATE_ROWS = "duplicate_rows"
JOIN_EXPLOSION = "join_explosion"
EXTRA_ROWS = "extra_rows"
MISSING_OPTIONAL = "missing_optional"
MISSING_ROWS = "missing_rows"
WRONG_VALUES = "wrong_values"
DIFFERENT_ROWS = "different_rows"

ALL_SYMPTOMS = (
    QUERY_ERROR, FORBIDDEN_FEATURE, OVERFITTED,
    WRONG_QUERY_TYPE, WRONG_ASK_ANSWER, WRONG_COLUMNS, WRONG_ORDER,
    MISSING_DISTINCT, DUPLICATE_ROWS, JOIN_EXPLOSION, EXTRA_ROWS,
    MISSING_OPTIONAL, MISSING_ROWS, WRONG_VALUES, DIFFERENT_ROWS,
)

# Student gets at least this many times the expected rows -> probably a
# disconnected pattern or a wrong join variable (cartesian product).
JOIN_EXPLOSION_FACTOR = 3

# Algebra operator names (as produced by rdflib).
OP_OPTIONAL = "LeftJoin"
OP_DISTINCT = "Distinct"


def diagnose(
    comparison: Comparison,
    reference_ops: set[str],
    student_ops: set[str],
) -> list[str]:
    if comparison.passed:
        return []

    problem = comparison.problem
    if problem == PROBLEM_QUERY_TYPE:
        return [WRONG_QUERY_TYPE]
    if problem == PROBLEM_ASK_ANSWER:
        return [WRONG_ASK_ANSWER]
    if problem in (PROBLEM_COLUMN_COUNT, PROBLEM_COLUMN_NAMES):
        return [WRONG_COLUMNS]
    if problem == PROBLEM_ORDER:
        return [WRONG_ORDER]

    # From here on: problem == PROBLEM_ROWS
    has_missing = bool(comparison.missing_rows)
    has_extra = bool(comparison.extra_rows)

    if has_extra and not has_missing:
        return [_diagnose_extra_rows(comparison, reference_ops, student_ops)]

    if has_missing and not has_extra:
        if OP_OPTIONAL in reference_ops and OP_OPTIONAL not in student_ops:
            return [MISSING_OPTIONAL]
        return [MISSING_ROWS]

    # Both missing and extra rows.
    if comparison.reference_count == comparison.student_count:
        return [WRONG_VALUES]
    return [DIFFERENT_ROWS]


def _diagnose_extra_rows(comparison: Comparison, reference_ops: set[str], student_ops: set[str]) -> str:
    if comparison.extra_rows_are_duplicates:
        if OP_DISTINCT in reference_ops and OP_DISTINCT not in student_ops:
            return MISSING_DISTINCT
        return DUPLICATE_ROWS

    expected = max(comparison.reference_count, 1)
    if comparison.student_count >= JOIN_EXPLOSION_FACTOR * expected:
        return JOIN_EXPLOSION

    return EXTRA_ROWS
