from __future__ import annotations

from app.parsers.nutrition_parser import (
    parse_nutrition,
    parse_value,
)


def test_parse_value_protein():

    text = (
        "Proteína Bruta 26%"
    )

    value, unit, alias = parse_value(
        text.lower(),
        [
            "proteína bruta",
        ],
    )

    assert value == 26.0
    assert unit == "%"
    assert alias == "proteína bruta"


def test_parse_value_fat():

    text = (
        "Extrato Etéreo 15%"
    )

    value, unit, alias = parse_value(
        text.lower(),
        [
            "extrato etéreo",
        ],
    )

    assert value == 15.0
    assert unit == "%"
    assert alias == "extrato etéreo"


def test_parse_value_with_comma():

    text = (
        "Fibra Bruta 3,5%"
    )

    value, unit, alias = parse_value(
        text.lower(),
        [
            "fibra bruta",
        ],
    )

    assert value == 3.5
    assert unit == "%"
    assert alias == "fibra bruta"


def test_parse_value_not_found():

    value, unit, alias = parse_value(
        "Sem informação",
        [
            "proteína",
        ],
    )

    assert value is None
    assert unit is None
    assert alias is None


def test_parse_nutrition_none():

    result = parse_nutrition(None)

    assert result == {}


def test_parse_protein():

    text = """
    Proteína Bruta 26%
    """

    result = parse_nutrition(text)

    assert (
        result["protein"]["value"]
        == 26.0
    )

    assert (
        result["protein"]["unit"]
        == "%"
    )


def test_parse_multiple_nutrients():

    text = """
    Proteína Bruta 26%
    Extrato Etéreo 15%
    Fibra Bruta 3%
    Umidade 10%
    """

    result = parse_nutrition(text)

    assert (
        result["protein"]["value"]
        == 26
    )

    assert (
        result["fat"]["value"]
        == 15
    )

    assert (
        result["fiber"]["value"]
        == 3
    )

    assert (
        result["moisture"]["value"]
        == 10
    )


def test_parse_calcium_range():

    text = """
    Cálcio Mín. 1,2%
    Cálcio Máx. 1,8%
    """

    result = parse_nutrition(text)

    assert (
        result["calcium_min"]["value"]
        == 1.2
    )

    assert (
        result["calcium_max"]["value"]
        == 1.8
    )


def test_parser_returns_all_expected_keys():

    result = parse_nutrition(
        ""
    )

    expected = {

        "protein",

        "fat",

        "fiber",

        "ash",

        "moisture",

        "calcium_min",

        "calcium_max",

        "phosphorus",

        "sodium",

        "potassium",

    }

    assert expected.issubset(
        result.keys()
    )


def test_missing_nutrients_are_none():

    result = parse_nutrition(
        "Proteína Bruta 25%"
    )

    assert (
        result["fat"]["value"]
        is None
    )

    assert (
        result["fiber"]["value"]
        is None
    )

    assert (
        result["ash"]["value"]
        is None
    )

    assert (
        result["protein"]["value"]
        == 25
    )


def test_parser_is_case_insensitive():

    result = parse_nutrition(
        "PROTEÍNA BRUTA 30%"
    )

    assert (
        result["protein"]["value"]
        == 30
    )


def test_parser_accepts_line_breaks():

    text = (
        "Proteína Bruta\n26%\n"
        "Extrato Etéreo\n15%"
    )

    result = parse_nutrition(
        text
    )

    assert (
        result["protein"]["value"]
        == 26
    )

    assert (
        result["fat"]["value"]
        == 15
    )