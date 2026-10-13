"""The only module that talks to rdflib.

Responsibilities:
  - load a dataset file into an rdflib Graph
  - run a query and convert the result into model.RawResult / model.Term
  - list the SPARQL algebra operators a query uses (for hints)
  - refuse unsafe features (SERVICE)

If you ever swap rdflib for another engine (pyoxigraph, a remote endpoint),
this is the only file that should need to change.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.util import guess_format

from .model import UNBOUND, RawResult, Term

log = logging.getLogger(__name__)

SUPPORTED_QUERY_TYPES = ("SELECT", "ASK")

# rdflib can execute SERVICE by calling remote endpoints over HTTP. A grader
# running student queries must never do that. This is a plain text check:
# it may also match the word SERVICE inside a string literal, which is an
# acceptable false positive for teaching katas.
_SERVICE_PATTERN = re.compile(r"\bSERVICE\b", re.IGNORECASE)


class QueryError(Exception):
    """The query could not be parsed or executed."""


def load_graph(path: Path) -> Graph:
    rdf_format = guess_format(str(path))
    if rdf_format is None:
        raise ValueError(f"Can't guess the RDF format of {path} (use .ttl, .nt, .rdf, .jsonld, ...)")
    graph = Graph()
    graph.parse(str(path), format=rdf_format)
    log.debug("Loaded %s (%s): %d triples", path, rdf_format, len(graph))
    return graph


def find_forbidden_feature(query_text: str) -> str | None:
    """Return the name of a forbidden feature used by the query, or None."""
    if _SERVICE_PATTERN.search(query_text):
        return "SERVICE"
    return None


def run_query(graph: Graph, query_text: str, prefixes: dict[str, str]) -> RawResult:
    """Run a SELECT or ASK query and return a RawResult.

    Raises QueryError for syntax errors, evaluation errors and unsupported
    query types. Iterating the rows happens inside the try block because
    rdflib may evaluate lazily, so errors can appear while reading rows.
    """
    if find_forbidden_feature(query_text):
        raise QueryError("SERVICE is not allowed")

    try:
        result = graph.query(query_text, initNs=prefixes)
        query_type = result.type

        if query_type == "ASK":
            raw = RawResult(query_type="ASK", ask_answer=bool(result.askAnswer))
        elif query_type == "SELECT":
            variables = [str(var) for var in result.vars]
            rows = [
                tuple(to_term(row[i]) for i in range(len(variables)))
                for row in result
            ]
            raw = RawResult(query_type="SELECT", variables=variables, rows=rows)
        else:
            raise QueryError(
                f"{query_type} queries are not supported yet; "
                f"supported: {', '.join(SUPPORTED_QUERY_TYPES)}"
            )
    except QueryError:
        raise
    except Exception as exc:  # rdflib raises many different exception types
        raise QueryError(f"{type(exc).__name__}: {exc}") from exc

    log.debug("Query returned %s with %d rows", raw.query_type, len(raw.rows))
    return raw


def to_term(node) -> Term:
    """Convert one rdflib node (or None for unbound) into a model.Term."""
    if node is None:
        return UNBOUND
    if isinstance(node, URIRef):
        return Term(kind="iri", value=str(node))
    if isinstance(node, BNode):
        return Term(kind="bnode", value=str(node))
    if isinstance(node, Literal):
        return Term(
            kind="literal",
            value=str(node),  # lexical form
            datatype=str(node.datatype) if node.datatype else None,
            lang=node.language,
        )
    raise TypeError(f"Unexpected value in query result: {node!r} ({type(node).__name__})")


def algebra_operators(query_text: str, prefixes: dict[str, str]) -> set[str]:
    """Return the names of all SPARQL algebra operators in a query.

    Example: a query with OPTIONAL and DISTINCT returns something like
    {"SelectQuery", "Project", "Distinct", "LeftJoin", "BGP", ...}.

    Returns an empty set if the query doesn't parse (the grader reports
    the syntax error separately).
    """
    try:
        prepared = prepareQuery(query_text, initNs=prefixes)
    except Exception as exc:
        log.debug("Could not build algebra: %s", exc)
        return set()

    names: set[str] = set()
    _collect_operator_names(prepared.algebra, names)
    return names


def _collect_operator_names(node, names: set[str]) -> None:
    """Walk rdflib's algebra tree (nested CompValue objects) and collect names."""
    if isinstance(node, CompValue):
        names.add(node.name)
        for child in node.values():
            _collect_operator_names(child, names)
    elif isinstance(node, (list, tuple)):
        for child in node:
            _collect_operator_names(child, names)
