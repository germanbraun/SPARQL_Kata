"""Turn RDF terms into plain, comparable strings.

Two results are considered equal when their normalized rows are equal, so
this module decides what "the same value" means. The rules:

    IRI                      -> <http://example.org/x>
    blank node               -> _:bnode   (all blank nodes compare equal, see note)
    unbound variable         -> UNBOUND
    plain / xsd:string       -> "text"
    language-tagged literal  -> "text"@es   (or "text" when ignore_lang=True)
    numeric literal          -> 5, 3.14     (any numeric datatype, rounded)
    other typed literal      -> "2024-01-01"^^<http://www.w3.org/2001/XMLSchema#date>

So "5"^^xsd:integer, "5.0"^^xsd:decimal and "5.0E0"^^xsd:double all become 5.

Note on blank nodes: their labels are arbitrary and differ between query
runs, so v0 treats them all as equal. Katas should avoid projecting
blank nodes in SELECT results.

The output strings are also what you see in reports and --debug output,
so they are designed to be readable.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from .model import RawResult, ResultSet, Row, Term

XSD = "http://www.w3.org/2001/XMLSchema#"
XSD_STRING = XSD + "string"

NUMERIC_DATATYPES = frozenset(
    XSD + name
    for name in (
        "integer", "decimal", "double", "float",
        "int", "long", "short", "byte",
        "nonNegativeInteger", "nonPositiveInteger",
        "positiveInteger", "negativeInteger",
        "unsignedInt", "unsignedLong", "unsignedShort", "unsignedByte",
    )
)


def normalize_result(raw: RawResult, ignore_lang: bool, decimal_places: int) -> ResultSet:
    """Normalize every row of a raw engine result."""
    rows = [normalize_row(row, ignore_lang, decimal_places) for row in raw.rows]
    return ResultSet(
        query_type=raw.query_type,
        variables=list(raw.variables),
        rows=rows,
        ask_answer=raw.ask_answer,
    )


def normalize_row(row: tuple[Term, ...], ignore_lang: bool = False, decimal_places: int = 6) -> Row:
    return tuple(normalize_term(term, ignore_lang, decimal_places) for term in row)


def normalize_term(term: Term, ignore_lang: bool = False, decimal_places: int = 6) -> str:
    if term.kind == "unbound":
        return "UNBOUND"
    if term.kind == "bnode":
        return "_:bnode"
    if term.kind == "iri":
        return f"<{term.value}>"
    if term.kind == "literal":
        return _normalize_literal(term, ignore_lang, decimal_places)
    raise ValueError(f"Unknown term kind: {term.kind!r}")


def _normalize_literal(term: Term, ignore_lang: bool, decimal_places: int) -> str:
    # json.dumps adds quotes and escapes inner quotes/newlines; keeps accents readable.
    quoted = json.dumps(term.value, ensure_ascii=False)

    if term.lang:
        if ignore_lang:
            return quoted
        return f"{quoted}@{term.lang.lower()}"

    if term.datatype in NUMERIC_DATATYPES:
        number = _normalize_number(term.value, decimal_places)
        if number is not None:
            return number
        # Not a valid number (e.g. "abc"^^xsd:integer): fall through and keep it typed.

    if term.datatype is None or term.datatype == XSD_STRING:
        return quoted

    return f"{quoted}^^<{term.datatype}>"


def _normalize_number(lexical: str, decimal_places: int) -> str | None:
    """Return a canonical string for a number, or None if it can't be parsed.

    Examples (decimal_places=6): "5" -> "5", "5.000" -> "5", "1.0E1" -> "10",
    "3.14159265" -> "3.141593".
    """
    try:
        number = Decimal(lexical.strip())
        if not number.is_finite():  # NaN, INF
            return None
        step = Decimal(1).scaleb(-decimal_places)  # 0.000001 for 6 places
        rounded = number.quantize(step).normalize()
    except InvalidOperation:
        return None

    if rounded == 0:
        return "0"  # avoids "-0"
    return format(rounded, "f")  # "f" avoids scientific notation like "1E+1"
