# sparql-kata

Grade SPARQL exercises by **what the query returns**, not by how it is written,
and give students hints about common mistakes (missing `OPTIONAL`, missing
`DISTINCT`, disconnected patterns, wrong `ORDER BY`, hardcoded answers...).

```
$ sparql-kata grade katas/optional-01.yaml my-solution.rq

Kata optional-01: Clientes y su email (si lo tienen)

  [FAIL] visible
         problem: rows
         expected 3 row(s), got 2
         missing (1):
           "Bruno" | UNBOUND
  [FAIL] hidden-1

Result: FAILED

Hints:
  - Algunos clientes no aparecen. ¿Qué pasa con los que no tienen email?
```

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Usage

```bash
sparql-kata show  katas/optional-01.yaml                  # print the exercise
sparql-kata grade katas/optional-01.yaml solution.rq      # grade a solution
sparql-kata check katas/optional-01.yaml                  # validate a kata (authors)

# options for all commands
--lang es|en     hint language (default: es)
--debug          show every intermediate step, including hidden datasets
```

`python -m sparql_kata ...` works too. Exit codes: `0` passed, `1` failed, `2` error,
so `grade` can run in CI.

Try the bundled examples:

```bash
sparql-kata grade katas/optional-01.yaml examples/optional-01/no-optional.rq
sparql-kata grade katas/distinct-01.yaml examples/distinct-01/hardcoded.rq
sparql-kata grade katas/join-01.yaml     examples/join-01/wrong-join.rq
```

## How grading works

1. Each dataset of the kata is loaded (visible first, then hidden ones).
2. The reference query and the student query both run on it.
3. Every value is **normalized** to a comparable string (see below).
4. Results are compared as **multisets of rows**: order is ignored unless the
   kata says `order_sensitive: true`; duplicates count.
5. Differences are **diagnosed** into symptom codes, which map to hint texts.

### Hidden datasets

A kata can have extra datasets that students don't see. A query that passes
the visible dataset but fails a hidden one gets the `overfitted` hint. This
catches hardcoded answers (`VALUES ?city { ... }`) and queries that only work
by accident on the sample data.

Note: hidden datasets are only really hidden if students can't read the files,
for example when grading runs in CI or on your machine.

### Normalization rules

| Value | Normalized as |
|---|---|
| IRI | `<http://example.org/x>` |
| blank node | `_:bnode` (all blank nodes compare equal) |
| unbound | `UNBOUND` |
| plain or `xsd:string` literal | `"text"` |
| language-tagged literal | `"text"@es`, or `"text"` with `ignore_lang: true` |
| any numeric literal | `5`, `3.14` (so `"5"^^xsd:integer` equals `"5.0E0"^^xsd:double`), rounded to `decimal_places` |
| other typed literal | `"2024-01-01"^^<...#date>` |

### Symptoms and hints

| Code | Detected when |
|---|---|
| `query_error` | the student query does not parse or fails |
| `forbidden_feature` | the query uses `SERVICE` (never executed) |
| `overfitted` | visible dataset passes, a hidden one fails |
| `wrong_query_type` | e.g. ASK instead of SELECT |
| `wrong_ask_answer` | ASK returns the wrong boolean |
| `wrong_columns` | different number of columns (or names, with `by_name`) |
| `wrong_order` | right rows, wrong order (`order_sensitive` katas) |
| `missing_distinct` | only repeated rows extra, reference uses DISTINCT and student doesn't |
| `duplicate_rows` | only repeated rows extra, otherwise |
| `join_explosion` | at least 3x the expected rows (disconnected patterns) |
| `extra_rows` | some rows extra, none missing |
| `missing_optional` | rows missing, reference uses OPTIONAL and student doesn't |
| `missing_rows` | rows missing, none extra |
| `wrong_values` | same row count, different values |
| `different_rows` | rows both missing and extra |

The checks for OPTIONAL and DISTINCT look at the **SPARQL algebra** of both
queries (`LeftJoin` and `Distinct` operators), not at the query text.

## Kata format

```yaml
id: optional-01                    # required
title: "Clientes y su email"
level: 2                           # free metadata
concepts: [OPTIONAL]               # free metadata
prompt: |                          # required
  Listá todos los clientes con su nombre y, si lo tienen, su email.

prefixes:                          # declared for every query; students can skip PREFIX
  ex: "http://example.org/crm/"

datasets:                          # paths relative to this YAML file
  visible: data/crm.ttl            # required
  hidden: [data/crm-hidden-1.ttl]  # optional, one or more

reference: |                       # or: reference_file: optional-01.rq
  SELECT ?name ?email WHERE {
    ?c a ex:Customer ; ex:name ?name .
    OPTIONAL { ?c ex:email ?email }
  }

grading:                           # all optional, defaults shown
  order_sensitive: false
  column_mapping: positional       # or by_name
  ignore_lang: false
  decimal_places: 6

hints:                             # optional overrides, per symptom code
  missing_optional:
    es: "¿Qué pasa con los clientes sin email?"
    en: "What happens to customers without an email?"
```

Unknown keys are rejected, so typos fail loudly. Always run
`sparql-kata check` on a new kata: it verifies the reference passes on every
dataset and warns when a hidden dataset gives the same results as the visible
one (and therefore can't catch overfitting).

## Code map (for debugging)

Each step of the pipeline is its own module, and only `engine.py` imports rdflib.

```
cli.py        argument parsing, commands, exit codes
kata.py       load + validate kata YAML               -> Kata
grader.py     runs the pipeline for each dataset      -> GradeReport
  engine.py     rdflib: load graph, run query        -> RawResult (Term objects)
  normalize.py  terms -> comparable strings          -> ResultSet
  compare.py    bag comparison                       -> Comparison
  hints.py      comparison + algebra -> symptom codes
messages.py   symptom code -> hint text (es/en)
report.py     GradeReport -> terminal text
model.py      plain dataclasses shared by all of the above
```

Debugging tips:

- `--debug` prints the normalized reference and student rows for every
  dataset, the algebra operators of both queries and the symptoms, and turns
  on `logging` at DEBUG level.
- `normalize`, `compare` and `hints` take plain Python data, so you can
  reproduce a problem in a REPL or a unit test without any RDF.
- To add a hint: add a code in `hints.py` (and to `ALL_SYMPTOMS`), a rule in
  `diagnose()`, and texts in `messages.py`. The import-time check in
  `messages.py` fails if a code has no message.

## Limitations (v0)

- SELECT and ASK only; CONSTRUCT/DESCRIBE are rejected.
- All blank nodes compare equal in SELECT results.
- The SERVICE check is textual, so the word inside a string literal is also rejected.
- Report labels are in English; only hints are localized.
- rdflib is fine for small teaching datasets but slow on large ones.

## License

MIT, see [LICENSE](LICENSE).
