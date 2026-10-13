"""Runs the example solutions through the real grader (needs rdflib)."""

from pathlib import Path

import pytest

pytest.importorskip("rdflib")

from sparql_kata import hints  # noqa: E402
from sparql_kata.grader import grade  # noqa: E402
from sparql_kata.kata import load_kata  # noqa: E402

ROOT = Path(__file__).parent.parent


def run(kata_name, solution_name):
    kata = load_kata(ROOT / "katas" / f"{kata_name}.yaml")
    query = (ROOT / "examples" / kata_name / f"{solution_name}.rq").read_text()
    return grade(kata, query)


@pytest.mark.parametrize("kata_name", ["optional-01", "distinct-01", "join-01", "filter-01", "regex-01", "not-exists-01"])
def test_reference_passes_itself(kata_name):
    kata = load_kata(ROOT / "katas" / f"{kata_name}.yaml")
    assert grade(kata, kata.reference).passed


@pytest.mark.parametrize("kata_name", ["optional-01", "distinct-01", "join-01", "filter-01", "regex-01", "not-exists-01"])
def test_correct_solutions_pass(kata_name):
    assert run(kata_name, "correct").passed


@pytest.mark.parametrize(
    "kata_name, solution, expected_first_symptom",
    [
        ("optional-01", "no-optional", hints.MISSING_OPTIONAL),
        ("optional-01", "syntax-error", hints.QUERY_ERROR),
        ("distinct-01", "no-distinct", hints.MISSING_DISTINCT),
        ("distinct-01", "hardcoded", hints.OVERFITTED),
        ("join-01", "wrong-join", hints.JOIN_EXPLOSION),
        ("join-01", "no-order", hints.WRONG_ORDER),
        ("filter-01", "no-filter", hints.EXTRA_ROWS),
        ("filter-01", "string-compare", hints.MISSING_ROWS),
        ("filter-01", "greater-or-equal", hints.OVERFITTED),
        ("regex-01", "no-anchor", hints.EXTRA_ROWS),
        ("regex-01", "case-sensitive", hints.OVERFITTED),
        ("not-exists-01", "unlinked-variable", hints.MISSING_ROWS),
        ("not-exists-01", "exists-instead", hints.DIFFERENT_ROWS),
    ],
)
def test_wrong_solutions_get_the_right_hint(kata_name, solution, expected_first_symptom):
    report = run(kata_name, solution)
    assert not report.passed
    assert report.symptoms[0] == expected_first_symptom


def test_service_is_rejected():
    kata = load_kata(ROOT / "katas" / "optional-01.yaml")
    report = grade(kata, "SELECT * WHERE { SERVICE <http://example.org/sparql> { ?s ?p ?o } }")
    assert report.symptoms == [hints.FORBIDDEN_FEATURE]
