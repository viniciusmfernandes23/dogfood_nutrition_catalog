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
    
    # Encontra o nutriente protein no dicionário
    protein_data = next((v for k, v in result.items() if v["nutrient"] == "protein"), None)
    assert protein_data is not None
    assert protein_data["value"] == 26.0
    assert protein_data["unit"] == "%"


def test_parse_multiple_nutrients():

    text = """
    Proteína Bruta 26%
    Extrato Etéreo 15%
    Fibra Bruta 3%
    Umidade 10%
    """

    result = parse_nutrition(text)
    
    nutrients = {v["nutrient"]: v["value"] for k, v in result.items()}
    assert nutrients["protein"] == 26
    assert nutrients["fat"] == 15
    assert nutrients["fiber"] == 3
    assert nutrients["moisture"] == 10


def test_parse_calcium_range():

    text = """
    Cálcio Mín. 1,2%
    Cálcio Máx. 1,8%
    """

    result = parse_nutrition(text)
    
    nutrients = {v["nutrient"]: v["value"] for k, v in result.items()}
    assert nutrients["calcium_min"] == 1.2
    assert nutrients["calcium_max"] == 1.8


def test_parser_returns_any_expected_keys():

    result = parse_nutrition(
        "Proteína Bruta 25%"
    )
    
    nutrients = {v["nutrient"] for k, v in result.items()}
    assert "protein" in nutrients


def test_parser_is_case_insensitive():

    result = parse_nutrition(
        "PROTEÍNA BRUTA 30%"
    )
    
    protein_data = next((v for k, v in result.items() if v["nutrient"] == "protein"), None)
    assert protein_data["value"] == 30


def test_parser_accepts_line_breaks():

    text = (
        "Proteína Bruta\n26%\n"
        "Extrato Etéreo\n15%"
    )

    result = parse_nutrition(
        text
    )
    
    nutrients = {v["nutrient"]: v["value"] for k, v in result.items()}
    assert nutrients["protein"] == 26
    assert nutrients["fat"] == 15

def test_parse_energy_kcal_100g():
    """
    Testa a captura de energia metabolizável com a unidade kcal/100g.
    """
    text = "Energia Metabolizável 350 kcal/100 g"
    result = parse_nutrition(text)
    
    energy_data = next((v for k, v in result.items() if v["nutrient"] == "metabolizable_energy"), None)
    assert energy_data is not None
    assert energy_data["value"] == 350.0
    assert energy_data["unit"] == "kcal/100g"

def test_parse_energy_mj_kg():
    """
    Testa a captura de energia metabolizável com a unidade MJ/kg.
    """
    text = "Energia Metabolizável 14,6 MJ / kg"
    result = parse_nutrition(text)
    
    energy_data = next((v for k, v in result.items() if v["nutrient"] == "metabolizable_energy"), None)
    assert energy_data is not None
    assert energy_data["value"] == 14.6
    assert energy_data["unit"] == "mj/kg"
