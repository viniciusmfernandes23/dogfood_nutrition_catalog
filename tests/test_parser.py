from __future__ import annotations

from app.parsers.nutrition_parser import (
    parse_nutrition,
    parse_value,
)
from app.parsers.html_parser import (
    extract_ingredients_section,
    extract_product_ratings,
    extract_guarantee_section,
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


def test_extract_ingredients_section():
    html = """
    <h3>Ingredientes</h3>
    <p>Farinha de frango, arroz integral, gordura de frango</p>
    <h3>Níveis de Garantia</h3>
    <p>Proteína Bruta 26%</p>
    """

    assert extract_ingredients_section(html) == (
        "Farinha de frango, arroz integral, gordura de frango"
    )


def test_extract_composicao_basica_as_ingredients():
    html = """
    <h3>Composição Básica</h3>
    <p>Carne de frango, glicerina vegetal e sorbato de potássio</p>
    <h3>Quantidade</h3>
    <p>100 g</p>
    """

    assert extract_ingredients_section(html) == (
        "Carne de frango, glicerina vegetal e sorbato de potássio"
    )


def test_extract_ingredients_stops_at_next_html_heading():
    html = """
    <h3>Composição Básica</h3>
    <p>Carne de frango e arroz</p>
    <h3>Quando dar petisco para cachorro?</h3>
    <p>Ofereça como recompensa.</p>
    """

    assert extract_ingredients_section(html) == "Carne de frango e arroz"


def test_extract_ingredients_from_compound_heading():
    html = """
    <h2>Qual a composição da ração?</h2>
    <h3>Ração Fórmula Natural Life: Ingredientes</h3>
    <p>Farinha de vísceras de aves, óleo de salmão e frutas desidratadas</p>
    <h3>Ração Fórmula Natural Life: Níveis de garantia</h3>
    <p>Proteína Bruta 28%</p>
    """

    assert extract_ingredients_section(html) == (
        "Farinha de vísceras de aves, óleo de salmão e frutas desidratadas"
    )


def test_extract_product_ratings_from_next_data():
        html = """
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"productDetail":{"productRating":{
            "avg":"4.80",
            "stars":{"1":168,"2":41,"3":154,"4":708,"5":7435}
        }}}}}
        </script>
        """

        assert extract_product_ratings(html) == {
                "rating_average": 4.8,
                "rating_count": 8506,
                "rating_1_star": 168,
                "rating_2_star": 41,
                "rating_3_star": 154,
                "rating_4_star": 708,
                "rating_5_star": 7435,
        }


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


def test_parse_calcium_range_ignores_calcium_in_ingredients():
    text = """
    Ingredientes: Minerais (Iodato de Cálcio).
    Níveis de Garantia
    Umidade (máx.)
    100 g/kg (10%)
    Cálcio (máx.)
    17 g/kg (1,7%)
    Cálcio (mín.)
    10 g/kg (1%)
    """

    result = parse_nutrition(text)
    calcium = {
        value["nutrient"]: value["value"]
        for value in result.values()
        if value["nutrient"] in {"calcium_min", "calcium_max"}
    }

    assert calcium == {"calcium_max": 17.0, "calcium_min": 10.0}


def test_guarantee_section_does_not_map_protein_as_chlorine():
    html = """
    <h3>Composição Básica</h3>
    <p>Amido de batata, carbonato de cálcio, clorofila.</p>
    <h3>Níveis de garantia</h3>
    <table>
        <tr><td>Proteína Bruta (mín.)</td><td>60 g/kg</td></tr>
        <tr><td>Matéria Mineral (máx.)</td><td>40 g/kg</td></tr>
    </table>
    """

    section = extract_guarantee_section(html)
    result = parse_nutrition(section)
    nutrients = {value["nutrient"]: value["value"] for value in result.values()}

    assert nutrients["protein"] == 60.0
    assert "chlorine" not in nutrients


def test_parser_does_not_map_vitamin_k_as_potassium():
    result = parse_nutrition("Vitamina K 30,07 mg/kg")
    nutrients = {value["nutrient"] for value in result.values()}

    assert "potassium" not in nutrients


def test_parser_separates_mos_fos_and_metabolizable_energy():
    result = parse_nutrition(
        "Energia metabolizável (MOS) (mín.) 300 mg/kg; "
        "Frutoligossacarídeos (FOS) (mín.) 1.000 mg/kg; "
        "Energia metabolizável (mín.) 3.620 kcal/kg"
    )
    nutrients = {value["nutrient"]: value for value in result.values()}

    assert nutrients["mos"]["value"] == 300.0
    assert nutrients["mos"]["unit"] == "mg/kg"
    assert nutrients["fos"]["value"] == 1000.0
    assert nutrients["fos"]["unit"] == "mg/kg"
    assert nutrients["metabolizable_energy"]["value"] == 3620.0
    assert nutrients["metabolizable_energy"]["unit"] == "kcal/kg"


def test_parser_does_not_map_generic_mg_as_magnesium():
    result = parse_nutrition("Ácido fólico: 0,05 mg")
    nutrients = {value["nutrient"] for value in result.values()}

    assert "magnesium" not in nutrients


def test_parser_does_not_map_otimos_as_mos_or_fosforo_as_fos():
    result = parse_nutrition(
        "Fórmula enriquecida com vitaminas e microminerais ótimos para a saúde. "
        "Ácido Fólico: 0,33 mg; Fósforo (mín.) 7.000 mg/kg"
    )
    nutrients = {value["nutrient"]: value for value in result.values()}

    assert "mos" not in nutrients
    assert "fos" not in nutrients
    assert nutrients["phosphorus"]["value"] == 7000.0


def test_parser_keeps_energy_kcal_unit_when_mj_is_also_present():
    result = parse_nutrition("Energia Metabolizável Kcal/Kg 3990 - Mj/Kg 16,69")
    energy = next(
        value for value in result.values()
        if value["nutrient"] == "metabolizable_energy"
    )

    assert energy["value"] == 3990.0
    assert energy["unit"] == "kcal/kg"


def test_parser_keeps_kcal_per_sachet_unit():
    result = parse_nutrition("Energia Metabolizável 72 kcal/sachê")
    energy = next(
        value for value in result.values()
        if value["nutrient"] == "metabolizable_energy"
    )

    assert energy["value"] == 72.0
    assert energy["unit"] == "kcal/sache"


def test_parser_ignores_energy_per_unit():
    result = parse_nutrition("Energia metabolizável 35 kcal/und")

    assert not any(
        value["nutrient"] == "metabolizable_energy"
        for value in result.values()
    )


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
