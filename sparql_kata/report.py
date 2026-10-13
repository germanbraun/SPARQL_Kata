"""Format a GradeReport as text for the terminal.

What students see:
  - PASS/FAIL per dataset
  - for the VISIBLE dataset only: counts and example missing/extra rows
  - hints

Hidden datasets never show their rows (that would reveal the answers),
unless --debug is on, which is meant for the kata author.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .messages import hint_text

if TYPE_CHECKING:  # avoids importing rdflib just to format text
    from .compare import Comparison
    from .grader import DatasetResult, GradeReport
    from .model import ResultSet, Row


def format_report(report: GradeReport, lang: str = "es", debug: bool = False, max_examples: int = 5) -> str:
    kata = report.kata
    lines = [f"Kata {kata.id}: {kata.title}", ""]

    if report.error:
        lines.append(f"  Rejected: {report.error}")

    for result in report.datasets:
        lines.extend(_format_dataset(result, debug, max_examples))

    if debug:
        lines.append("")
        lines.append(f"  [debug] reference algebra: {sorted(report.reference_ops)}")
        lines.append(f"  [debug] student algebra:   {sorted(report.student_ops)}")
        lines.append(f"  [debug] symptoms:          {report.symptoms}")

    lines.append("")
    if report.passed:
        lines.append("Result: PASSED")
    else:
        lines.append("Result: FAILED")
        if report.symptoms:
            lines.append("")
            lines.append("Hints:")
            for code in report.symptoms:
                lines.append(f"  - {hint_text(code, lang, kata.hints)}")
    return "\n".join(lines)


def _format_dataset(result: DatasetResult, debug: bool, max_examples: int) -> list[str]:
    status = "PASS" if result.passed else "FAIL"
    lines = [f"  [{status}] {result.dataset.label}"]
    show_details = debug or not result.dataset.hidden

    if result.error and show_details:
        lines.append(f"         error: {result.error}")

    if result.comparison and not result.passed and show_details:
        lines.extend(_format_comparison(result.comparison, max_examples))

    if debug:
        lines.append(f"         [debug] file: {result.dataset.path}")
        if result.reference:
            lines.extend(_format_result_set("reference", result.reference))
        if result.student:
            lines.extend(_format_result_set("student", result.student))
    return lines


def _format_comparison(comparison: Comparison, max_examples: int) -> list[str]:
    lines = [
        f"         problem: {comparison.problem}",
        f"         expected {comparison.reference_count} row(s), got {comparison.student_count}",
    ]
    lines.extend(_format_rows("missing", comparison.missing_rows, max_examples))
    lines.extend(_format_rows("extra", comparison.extra_rows, max_examples))
    return lines


def _format_rows(label: str, rows: list[Row], max_examples: int) -> list[str]:
    if not rows:
        return []
    lines = [f"         {label} ({len(rows)}):"]
    for row in rows[:max_examples]:
        lines.append(f"           {' | '.join(row)}")
    if len(rows) > max_examples:
        lines.append(f"           ... and {len(rows) - max_examples} more")
    return lines


def _format_result_set(label: str, result: ResultSet) -> list[str]:
    if result.query_type == "ASK":
        return [f"         [debug] {label}: ASK -> {result.ask_answer}"]
    lines = [f"         [debug] {label}: {result.variables} ({len(result.rows)} rows)"]
    for row in result.rows:
        lines.append(f"           {' | '.join(row)}")
    return lines
