# Onboarding: install and run sparql-kata

This guide takes you from a fresh clone to grading your first SPARQL query.
For how grading works internally and the full kata format, see the
[README](README.md).

## 1. Prerequisites

- **Python 3.10 or newer** (`python3 --version`)
- **git**

No triple store or internet connection is needed to grade: queries run
in memory with [rdflib](https://rdflib.readthedocs.io/).

## 2. Get the code

```bash
git clone https://github.com/germanbraun/SPARQL_Kata.git
cd SPARQL_Kata
```

## 3. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

Run `source .venv/bin/activate` again in every new terminal before using the tool.

## 4. Install

Pick one option.

**Option A, recommended:** install the package. This also gives you the
`sparql-kata` command.

```bash
pip install -e ".[dev]"
```

**Option B:** install only the dependencies from the requirements files.

```bash
pip install -r requirements-dev.txt   # or requirements.txt without pytest
```

With option B there is no `sparql-kata` command. Run the tool as
`python -m sparql_kata ...` from the repository root instead.

## 5. Check the install

```bash
pytest
```

All tests should pass (`44 passed`). Then:

```bash
sparql-kata --help
```

## 6. Your first kata

Read the exercise:

```bash
sparql-kata show katas/optional-01.yaml
```

```
optional-01: Clientes y su email (si lo tienen)

Listá todos los clientes (ex:Customer) con su nombre (ex:name) y,
si lo tienen, su email (ex:email).
Columnas: nombre, email.

Prefixes (already declared, you don't need PREFIX lines):
  ex: <http://example.org/crm/>
  xsd: <http://www.w3.org/2001/XMLSchema#>

Sample data: katas/data/crm.ttl
```

Write your answer in a `.rq` file, for example `my-solution.rq`:

```sparql
SELECT ?name ?email WHERE {
  ?customer a ex:Customer ;
            ex:name ?name ;
            ex:email ?email .
}
```

Grade it:

```bash
sparql-kata grade katas/optional-01.yaml my-solution.rq
```

```
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

Fix the query by wrapping the email pattern in `OPTIONAL { ... }` and grade
again. You should see `Result: PASSED`.

Hints are in Spanish by default. Add `--lang en` for English.

## 7. Everyday commands

| Command | What it does |
|---|---|
| `sparql-kata show KATA.yaml` | print the exercise |
| `sparql-kata grade KATA.yaml SOLUTION.rq` | grade a solution |
| `sparql-kata check KATA.yaml` | validate a kata you wrote |

Options for every command:

- `--lang es|en` sets the hint language.
- `--debug` prints every intermediate step, including the hidden datasets.

Exit codes are `0` for passed, `1` for failed and `2` for an error, so
`grade` can be used in scripts and CI.

## 8. Try the bundled examples

`examples/` has a correct solution and some typical mistakes for each sample kata:

```bash
sparql-kata grade katas/optional-01.yaml examples/optional-01/correct.rq
sparql-kata grade katas/optional-01.yaml examples/optional-01/no-optional.rq
sparql-kata grade katas/distinct-01.yaml examples/distinct-01/hardcoded.rq
sparql-kata grade katas/join-01.yaml     examples/join-01/wrong-join.rq
```

## 9. Writing your own kata

1. Copy `katas/optional-01.yaml` and edit it. The format is documented in
   the [README](README.md#kata-format).
2. Put the Turtle data under `katas/data/`. Add at least one **hidden**
   dataset that differs from the visible one, so hardcoded answers get caught.
3. Validate it:

   ```bash
   sparql-kata check katas/my-kata.yaml
   ```

   This confirms that the reference query passes on every dataset. It also
   warns when a hidden dataset returns the same results as the visible one.

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found: sparql-kata` | Activate the venv (`source .venv/bin/activate`), or use option A in step 4. |
| `ModuleNotFoundError: rdflib` / `yaml` | Activate the venv and install again (step 4). |
| `Kata error: ... unknown key(s) [...]` | A typo in the kata YAML. Unknown keys are rejected on purpose. |
| Unexpected grading result | Run again with `--debug` to see both queries' normalized rows and the detected symptoms. |
| Query with `SERVICE` is rejected | This is intended. Federated queries are never executed. |
