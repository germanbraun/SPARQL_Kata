"""Plain data classes shared by the whole pipeline.

This module deliberately does NOT import rdflib. Only `engine.py` talks to
rdflib; it converts rdflib objects into the simple classes below. Everything
after that (normalize, compare, hints, report) works on plain Python data,
so you can test and debug those steps without an RDF store.

Pipeline overview:

    engine.run_query()        -> RawResult   (rows of Term objects)
    normalize.normalize_result() -> ResultSet (rows of plain strings)
    compare.compare_results()    -> Comparison
    hints.diagnose()             -> list of symptom codes
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Term:
    """One RDF term from a query result, independent of rdflib.

    kind is one of: "iri", "bnode", "literal", "unbound".
    For literals, `datatype` and `lang` may be set.
    """

    kind: str
    value: str = ""
    datatype: str | None = None
    lang: str | None = None


UNBOUND = Term(kind="unbound")


@dataclass
class RawResult:
    """A query result as returned by the engine, before normalization."""

    query_type: str  # "SELECT" or "ASK"
    variables: list[str] = field(default_factory=list)  # SELECT only, in projection order
    rows: list[tuple[Term, ...]] = field(default_factory=list)
    ask_answer: bool | None = None  # ASK only


# A normalized row: one readable string per column, e.g. ("<http://ex/ana>", '"Ana"', "UNBOUND")
Row = tuple[str, ...]


@dataclass
class ResultSet:
    """A normalized query result. This is what gets compared."""

    query_type: str
    variables: list[str] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    ask_answer: bool | None = None
