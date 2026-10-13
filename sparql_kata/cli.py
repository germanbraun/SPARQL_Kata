"""Command-line interface.

    sparql-kata show  KATA.yaml                 print the exercise
    sparql-kata grade KATA.yaml SOLUTION.rq     grade a student query
    sparql-kata check KATA.yaml                 sanity-check a kata (for authors)

Common options: --lang es|en, --debug

Exit codes (useful in CI): 0 = passed / kata OK, 1 = failed, 2 = error.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .kata import KataError, load_kata
from .messages import DEFAULT_LANG

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        return args.handler(args)
    except KataError as exc:
        print(f"Kata error: {exc}", file=sys.stderr)
        return EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lang", default=DEFAULT_LANG, help=f"hint language (default: {DEFAULT_LANG})")
    common.add_argument("--debug", action="store_true",
                        help="show every intermediate step, including hidden datasets")

    parser = argparse.ArgumentParser(prog="sparql-kata", description="Grade SPARQL exercises by their results.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    show = subcommands.add_parser("show", parents=[common], help="print a kata's prompt")
    show.add_argument("kata", type=Path)
    show.set_defaults(handler=cmd_show)

    grade = subcommands.add_parser("grade", parents=[common], help="grade a solution file")
    grade.add_argument("kata", type=Path)
    grade.add_argument("solution", type=Path, help="file with the student's SPARQL query")
    grade.set_defaults(handler=cmd_grade)

    check = subcommands.add_parser("check", parents=[common], help="check that a kata is well-formed")
    check.add_argument("kata", type=Path)
    check.set_defaults(handler=cmd_check)

    return parser


def cmd_show(args: argparse.Namespace) -> int:
    kata = load_kata(args.kata)
    print(f"{kata.id}: {kata.title}\n")
    print(kata.prompt.strip())
    if kata.prefixes:
        print("\nPrefixes (already declared, you don't need PREFIX lines):")
        for prefix, iri in kata.prefixes.items():
            print(f"  {prefix}: <{iri}>")
    print(f"\nSample data: {kata.datasets[0].path}")
    return EXIT_OK


def cmd_grade(args: argparse.Namespace) -> int:
    # Imported here so `show` works even before rdflib is installed.
    from .grader import grade
    from .report import format_report

    kata = load_kata(args.kata)
    if not args.solution.is_file():
        print(f"Solution file not found: {args.solution}", file=sys.stderr)
        return EXIT_ERROR

    student_query = args.solution.read_text(encoding="utf-8")
    report = grade(kata, student_query)
    print(format_report(report, lang=args.lang, debug=args.debug))
    return EXIT_OK if report.passed else EXIT_FAILED


def cmd_check(args: argparse.Namespace) -> int:
    """Grade the reference against itself and warn about weak datasets."""
    from .grader import grade

    kata = load_kata(args.kata)
    report = grade(kata, kata.reference)  # raises KataError if the reference fails

    if not report.passed:
        print("Kata error: the reference query does not pass its own grading", file=sys.stderr)
        return EXIT_ERROR

    print(f"Kata {kata.id}: OK")
    visible_rows = report.datasets[0].reference.rows
    for result in report.datasets:
        reference = result.reference
        if reference.query_type == "ASK":
            print(f"  {result.dataset.label}: ASK -> {reference.ask_answer}  ({result.dataset.path})")
            continue

        rows = reference.rows
        print(f"  {result.dataset.label}: {len(rows)} row(s)  ({result.dataset.path})")
        if not rows:
            print("    warning: the reference returns no rows here")
        if result.dataset.hidden and sorted(rows) == sorted(visible_rows):
            print("    warning: same results as the visible dataset, so it can't catch overfitting")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
