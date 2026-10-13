from sparql_kata.model import Term, UNBOUND
from sparql_kata.normalize import XSD, normalize_term


def literal(value, datatype=None, lang=None):
    return Term(kind="literal", value=value, datatype=datatype, lang=lang)


def test_iri_bnode_unbound():
    assert normalize_term(Term("iri", "http://ex/a")) == "<http://ex/a>"
    assert normalize_term(Term("bnode", "N123")) == normalize_term(Term("bnode", "N999"))
    assert normalize_term(UNBOUND) == "UNBOUND"


def test_numbers_of_different_types_are_equal():
    as_integer = normalize_term(literal("5", XSD + "integer"))
    as_decimal = normalize_term(literal("5.000", XSD + "decimal"))
    as_double = normalize_term(literal("5.0E0", XSD + "double"))
    assert as_integer == as_decimal == as_double == "5"


def test_numbers_are_rounded():
    assert normalize_term(literal("3.14159265", XSD + "decimal"), decimal_places=2) == "3.14"
    assert normalize_term(literal("1.0E1", XSD + "double")) == "10"
    assert normalize_term(literal("-0.0000001", XSD + "double")) == "0"


def test_number_is_not_equal_to_string():
    assert normalize_term(literal("5", XSD + "integer")) != normalize_term(literal("5"))


def test_invalid_number_stays_typed():
    assert normalize_term(literal("abc", XSD + "integer")) == f'"abc"^^<{XSD}integer>'


def test_plain_string_equals_xsd_string():
    assert normalize_term(literal("Ana")) == normalize_term(literal("Ana", XSD + "string")) == '"Ana"'


def test_language_tags():
    tagged = literal("Ana", lang="ES")
    assert normalize_term(tagged) == '"Ana"@es'
    assert normalize_term(tagged, ignore_lang=True) == '"Ana"'


def test_other_typed_literal():
    assert normalize_term(literal("2024-01-01", XSD + "date")) == f'"2024-01-01"^^<{XSD}date>'
