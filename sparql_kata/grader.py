"""Grade a student query against a kata.

For each dataset (visible first, then hidden):
    1. load the graph
    2. run the reference query  -> normalize
    3. run the student query    -> normalize
    4. compare                  -> Comparison
    5. diagnose                 -> symptom codes

Then combine the per-dataset results into a GradeReport. The report keeps
the intermediate results (normalized reference and student results, the
algebra operators) so --debug can show every step.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from . import engine, hints
from .compare import Comparison, compare_results
from .kata import Dataset, Kata, KataError
from .model import ResultSet
from .normalize import normalize_result

log = logging.getLogger(__name__)


@dataclass
class DatasetResult:
    dataset: Dataset
    passed: bool
    symptoms: list[str] = field(default_factory=list)
    comparison: Comparison | None = None
    error: str | None = None             # student query error on this dataset
    reference: ResultSet | None = None   # kept for --debug
    student: ResultSet | None = None     # kept for --debug


@dataclass
class GradeReport:
    kata: Kata
    passed: bool
    datasets: list[DatasetResult] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)  # unique, most important first
    error: str | None = None                            # query rejected before running
    reference_ops: set[str] = field(default_factory=set)
    student_ops: set[str] = field(default_factory=set)


def grade(kata: Kata, student_query: str) -> GradeReport:
    forbidden = engine.find_forbidden_feature(student_query)
    if forbidden:
        return GradeReport(
            kata=kata,
            passed=False,
            symptoms=[hints.FORBIDDEN_FEATURE],
            error=f"{forbidden} is not allowed",
        )

    reference_ops = engine.algebra_operators(kata.reference, kata.prefixes)
    student_ops = engine.algebra_operators(student_query, kata.prefixes)
    log.debug("Reference algebra operators: %s", sorted(reference_ops))
    log.debug("Student algebra operators:   %s", sorted(student_ops))

    results = [
        grade_on_dataset(kata, dataset, student_query, reference_ops, student_ops)
        for dataset in kata.datasets
    ]

    return GradeReport(
        kata=kata,
        passed=all(result.passed for result in results),
        datasets=results,
        symptoms=collect_symptoms(results),
        reference_ops=reference_ops,
        student_ops=student_ops,
    )


def grade_on_dataset(
    kata: Kata,
    dataset: Dataset,
    student_query: str,
    reference_ops: set[str],
    student_ops: set[str],
) -> DatasetResult:
    log.debug("--- Dataset %s: %s", dataset.label, dataset.path)
    options = kata.grading

    try:
        graph = engine.load_graph(dataset.path)
    except Exception as exc:
        raise KataError(f"Can't load dataset {dataset.path}: {exc}") from exc

    # A failing reference query is the kata author's problem, not the student's.
    try:
        reference_raw = engine.run_query(graph, kata.reference, kata.prefixes)
    except engine.QueryError as exc:
        raise KataError(f"The reference query fails on {dataset.path}: {exc}") from exc
    reference = normalize_result(reference_raw, options.ignore_lang, options.decimal_places)

    try:
        student_raw = engine.run_query(graph, student_query, kata.prefixes)
    except engine.QueryError as exc:
        log.debug("Student query failed: %s", exc)
        return DatasetResult(
            dataset=dataset,
            passed=False,
            symptoms=[hints.QUERY_ERROR],
            error=str(exc),
            reference=reference,
        )
    student = normalize_result(student_raw, options.ignore_lang, options.decimal_places)

    comparison = compare_results(reference, student, options.order_sensitive, options.column_mapping)
    symptoms = hints.diagnose(comparison, reference_ops, student_ops)
    log.debug("Comparison: %s", comparison)
    log.debug("Symptoms: %s", symptoms)

    return DatasetResult(
        dataset=dataset,
        passed=comparison.passed,
        symptoms=symptoms,
        comparison=comparison,
        reference=reference,
        student=student,
    )


def collect_symptoms(results: list[DatasetResult]) -> list[str]:
    """Merge per-dataset symptoms into one ordered list without duplicates.

    If the visible dataset passes but a hidden one fails, the query is
    probably tailored to the sample data: OVERFITTED goes first.
    """
    symptoms: list[str] = []

    visible_passed = results[0].passed if results else False
    hidden_failed = any(not r.passed for r in results if r.dataset.hidden)
    if visible_passed and hidden_failed:
        symptoms.append(hints.OVERFITTED)

    for result in results:
        for symptom in result.symptoms:
            if symptom not in symptoms:
                symptoms.append(symptom)
    return symptoms
