# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Project: sparql-kata

A Python CLI that grades SPARQL exercises ("katas") by comparing query results.
See [README.md](README.md) for the kata format and grading rules.

**Commands** (inside the `.venv`):
- `pip install -e ".[dev]"`: install
- `pytest`: run all tests
- `sparql-kata check katas/<kata>.yaml`: validate a kata. CI runs this for every kata.

**Pipeline:** `engine → normalize → compare → hints → report`, one module per step in `sparql_kata/`.

**Rules:**
- Only `engine.py` imports rdflib. Everything after it works on plain Python data, so keep it that way.
- Code must run on Python 3.10, the oldest version CI tests.
- To add a hint: add the code to `ALL_SYMPTOMS` in `hints.py`, a rule in `diagnose()`, and `es`/`en` texts in `messages.py`. An import-time assert fails if a message is missing.
- Hints default to Spanish (`es`), with English as the fallback.
- Never execute student queries that use `SERVICE`.
- Keep `requirements.txt` in sync with the dependencies in `pyproject.toml`.
