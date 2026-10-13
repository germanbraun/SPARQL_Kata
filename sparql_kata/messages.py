"""Hint texts shown to students, per symptom code and language.

A kata can override any of these in its YAML `hints:` section, either with
a single string (used for every language) or with {es: ..., en: ...}.
"""

from __future__ import annotations

from . import hints as h

DEFAULT_LANG = "es"
FALLBACK_LANG = "en"

MESSAGES: dict[str, dict[str, str]] = {
    h.QUERY_ERROR: {
        "es": "Tu consulta no se pudo ejecutar. Revisá la sintaxis: llaves, puntos al final de cada patrón y prefijos.",
        "en": "Your query could not be run. Check the syntax: braces, dots after each pattern, and prefixes.",
    },
    h.FORBIDDEN_FEATURE: {
        "es": "La consulta usa SERVICE, que no está permitido en los ejercicios.",
        "en": "The query uses SERVICE, which is not allowed in the exercises.",
    },
    h.OVERFITTED: {
        "es": "Tu consulta funciona con los datos de ejemplo, pero no con otros datos. Evitá valores fijos y escribí una consulta general.",
        "en": "Your query works on the sample data but not on other data. Avoid hardcoded values and write a general query.",
    },
    h.WRONG_QUERY_TYPE: {
        "es": "El ejercicio espera otro tipo de consulta (por ejemplo, SELECT en lugar de ASK).",
        "en": "The exercise expects a different query form (for example SELECT instead of ASK).",
    },
    h.WRONG_ASK_ANSWER: {
        "es": "Tu ASK devuelve el valor opuesto al esperado. Revisá las condiciones del patrón.",
        "en": "Your ASK returns the opposite of the expected answer. Check the pattern conditions.",
    },
    h.WRONG_COLUMNS: {
        "es": "Las columnas no coinciden con lo pedido. Revisá qué variables proyectás en el SELECT.",
        "en": "The columns don't match what was asked. Check which variables you project in SELECT.",
    },
    h.WRONG_ORDER: {
        "es": "Los resultados son correctos, pero el orden no. Revisá el ORDER BY.",
        "en": "The results are right but the order is not. Check your ORDER BY.",
    },
    h.MISSING_DISTINCT: {
        "es": "Aparecen filas repetidas. ¿Cómo podés pedir que cada resultado aparezca una sola vez?",
        "en": "Some rows are repeated. How can you ask for each result to appear only once?",
    },
    h.DUPLICATE_ROWS: {
        "es": "Aparecen filas repetidas. Revisá si algún patrón genera más combinaciones de las necesarias.",
        "en": "Some rows are repeated. Check whether a pattern produces more combinations than needed.",
    },
    h.JOIN_EXPLOSION: {
        "es": "Obtenés muchas más filas de las esperadas. ¿Están todos tus patrones conectados por variables compartidas?",
        "en": "You get far more rows than expected. Are all your patterns connected through shared variables?",
    },
    h.EXTRA_ROWS: {
        "es": "Obtenés filas de más. Quizás falta una condición o un FILTER.",
        "en": "You get too many rows. Maybe a condition or FILTER is missing.",
    },
    h.MISSING_OPTIONAL: {
        "es": "Faltan resultados: algunas entidades desaparecen cuando no tienen cierta propiedad. ¿Cómo hacés que un patrón sea opcional?",
        "en": "Results are missing: some entities disappear when they lack a property. How can you make a pattern optional?",
    },
    h.MISSING_ROWS: {
        "es": "Faltan resultados. Puede que alguna condición o FILTER sea demasiado estricta.",
        "en": "Some results are missing. A condition or FILTER may be too strict.",
    },
    h.WRONG_VALUES: {
        "es": "Tenés la cantidad correcta de filas, pero algunos valores no coinciden. Revisá qué propiedad o variable devolvés.",
        "en": "You have the right number of rows but some values differ. Check which property or variable you return.",
    },
    h.DIFFERENT_ROWS: {
        "es": "Los resultados difieren de lo esperado: faltan algunas filas y sobran otras.",
        "en": "The results differ from the expected ones: some rows are missing and others are extra.",
    },
}

# Every symptom must have a message; fail fast at import time if one is forgotten.
_missing_messages = set(h.ALL_SYMPTOMS) - set(MESSAGES)
assert not _missing_messages, f"No message defined for: {sorted(_missing_messages)}"


def hint_text(code: str, lang: str = DEFAULT_LANG, overrides: dict | None = None) -> str:
    """Return the hint for a symptom code, preferring the kata's override."""
    if overrides and code in overrides:
        override = overrides[code]
        if isinstance(override, str):
            return override
        if lang in override:
            return override[lang]
        # Override exists but not in this language: fall back to the defaults below.

    texts = MESSAGES.get(code, {})
    return texts.get(lang) or texts.get(FALLBACK_LANG) or code
