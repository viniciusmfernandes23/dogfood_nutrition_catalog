"""
Testes de regressão para o bug de fator ×10 causado pela fragmentação do
separador decimal em quebras de linha pelo BeautifulSoup.

Cenário do bug:
    HTML: <td>7</td><td>,5</td><td>%</td>
    BeautifulSoup.get_text("\n") → "7\n,5\n%"
    Parser sem correção: captura "7" → 7.0 → 7% × 10 = 70 g/kg (ERRADO)
    Parser com correção: normaliza "7\n,5\n%" → "7,5\n%" → captura "7,5" → 7.5 → 7.5% × 10 = 75 g/kg (CORRETO)

Referência: auditoria fact_nutrient.csv — erro sistemático de fator ×10.
"""
from __future__ import annotations

import pytest

from app.parsers.html_parser import _normalize_split_decimals, extract_guarantee_section
from app.parsers.nutrition_parser import clean_numeric_value, parse_nutrition


# ---------------------------------------------------------------------------
# Testes de _normalize_split_decimals
# ---------------------------------------------------------------------------

class TestNormalizeSplitDecimals:
    """Verifica a reconstituição de números decimais fragmentados por \\n."""

    def test_comma_decimal_split_by_newline(self):
        assert _normalize_split_decimals("7\n,5%") == "7,5%"

    def test_comma_decimal_split_by_newline_with_spaces(self):
        assert _normalize_split_decimals("7 \n ,5%") == "7,5%"

    def test_dot_thousand_split_by_newline(self):
        assert _normalize_split_decimals("4\n.052 kcal/kg") == "4.052 kcal/kg"

    def test_dot_thousand_split_by_newline_3700(self):
        assert _normalize_split_decimals("3\n.700 kcal/kg") == "3.700 kcal/kg"

    def test_zero_comma_split(self):
        assert _normalize_split_decimals("0\n,2%") == "0,2%"

    def test_26_comma_split(self):
        assert _normalize_split_decimals("26\n,0%") == "26,0%"

    def test_no_change_when_intact(self):
        """Textos sem fragmentação não devem ser alterados."""
        assert _normalize_split_decimals("7,5%") == "7,5%"
        assert _normalize_split_decimals("4.052 kcal/kg") == "4.052 kcal/kg"
        assert _normalize_split_decimals("26,0%") == "26,0%"

    def test_idempotent(self):
        """Aplicar duas vezes deve produzir o mesmo resultado."""
        text = "7\n,5%"
        once = _normalize_split_decimals(text)
        twice = _normalize_split_decimals(once)
        assert once == twice


# ---------------------------------------------------------------------------
# Testes de clean_numeric_value
# ---------------------------------------------------------------------------

class TestCleanNumericValue:
    """Verifica que a vírgula decimal nunca é removida silenciosamente."""

    def test_comma_decimal_7_5(self):
        assert clean_numeric_value("7,5") == 7.5

    def test_comma_decimal_1_5(self):
        assert clean_numeric_value("1,5") == 1.5

    def test_comma_decimal_0_2(self):
        assert clean_numeric_value("0,2") == 0.2

    def test_comma_decimal_26_0(self):
        assert clean_numeric_value("26,0") == 26.0

    def test_dot_thousand_4052(self):
        assert clean_numeric_value("4.052") == 4052.0

    def test_dot_thousand_3700(self):
        assert clean_numeric_value("3.700") == 3700.0

    def test_dot_decimal_7_5(self):
        assert clean_numeric_value("7.5") == 7.5

    def test_dot_decimal_7_50(self):
        assert clean_numeric_value("7.50") == 7.5

    def test_dot_decimal_40_52(self):
        assert clean_numeric_value("40.52") == 40.52

    def test_integer_75(self):
        assert clean_numeric_value("75") == 75.0

    def test_br_full_1055_15(self):
        assert clean_numeric_value("1.055,15") == 1055.15


# ---------------------------------------------------------------------------
# Testes de parse_nutrition com texto fragmentado
# ---------------------------------------------------------------------------

class TestParseNutritionDecimalSplitFix:
    """
    Verifica que o parse_nutrition, após normalização pelo html_parser,
    captura corretamente valores com separador decimal fragmentado.
    """

    def _parse_normalized(self, raw_text: str) -> dict:
        """Normaliza o texto e depois faz o parse."""
        normalized = _normalize_split_decimals(raw_text)
        return parse_nutrition(normalized)

    def test_protein_7_5_percent_fragmented(self):
        result = self._parse_normalized("Proteína Bruta\nmín.\n7\n,5\n%")
        proteins = [v for v in result.values() if v["nutrient"] == "protein"]
        assert proteins, "Proteína não capturada"
        assert proteins[0]["value"] == 7.5
        assert proteins[0]["unit"] == "%"

    def test_fat_1_5_percent_fragmented(self):
        result = self._parse_normalized("Gordura Bruta\nmín.\n1\n,5\n%")
        fats = [v for v in result.values() if v["nutrient"] == "fat"]
        assert fats, "Gordura não capturada"
        assert fats[0]["value"] == 1.5
        assert fats[0]["unit"] == "%"

    def test_fiber_0_2_percent_fragmented(self):
        result = self._parse_normalized("Fibra Bruta\nmáx.\n0\n,2\n%")
        fibers = [v for v in result.values() if v["nutrient"] == "fiber"]
        assert fibers, "Fibra não capturada"
        assert fibers[0]["value"] == 0.2
        assert fibers[0]["unit"] == "%"

    def test_protein_26_0_percent_fragmented(self):
        result = self._parse_normalized("Proteína Bruta\nmín.\n26\n,0\n%")
        proteins = [v for v in result.values() if v["nutrient"] == "protein"]
        assert proteins, "Proteína não capturada"
        assert proteins[0]["value"] == 26.0
        assert proteins[0]["unit"] == "%"

    def test_energy_4052_kcalkg_fragmented(self):
        result = self._parse_normalized(
            "Energia Metabolizável\nmín.\n4\n.052\nkcal/kg"
        )
        energies = [v for v in result.values() if v["nutrient"] == "metabolizable_energy"]
        assert energies, "Energia não capturada"
        assert energies[0]["value"] == 4052.0
        assert energies[0]["unit"] == "kcal/kg"

    def test_energy_3700_kcalkg_fragmented(self):
        result = self._parse_normalized(
            "Energia Metabolizável\nmín.\n3\n.700\nkcal/kg"
        )
        energies = [v for v in result.values() if v["nutrient"] == "metabolizable_energy"]
        assert energies, "Energia não capturada"
        assert energies[0]["value"] == 3700.0
        assert energies[0]["unit"] == "kcal/kg"

    def test_intact_values_unchanged(self):
        """Valores sem fragmentação devem continuar funcionando."""
        result = parse_nutrition(
            "Proteína Bruta (mín.) 7,5%\n"
            "Gordura Bruta (mín.) 1,5%\n"
            "Energia Metabolizável (mín.) 4.052 kcal/kg"
        )
        proteins = [v for v in result.values() if v["nutrient"] == "protein"]
        fats = [v for v in result.values() if v["nutrient"] == "fat"]
        energies = [v for v in result.values() if v["nutrient"] == "metabolizable_energy"]
        assert proteins[0]["value"] == 7.5
        assert fats[0]["value"] == 1.5
        assert energies[0]["value"] == 4052.0

    def test_no_x10_factor_after_fix(self):
        """
        Garante que o valor capturado NÃO é ×10 do correto.
        Antes da correção: "7\n,5%" → capturava "7" → 7.0 (×10 de 0.7, não ×10 de 7.5)
        Após a correção:   "7\n,5%" → normaliza para "7,5%" → captura "7,5" → 7.5
        """
        result = self._parse_normalized("Gordura Bruta\nmín.\n1\n,5\n%")
        fats = [v for v in result.values() if v["nutrient"] == "fat"]
        assert fats, "Gordura não capturada"
        # O valor NÃO deve ser 15 (que seria ×10 de 1.5)
        assert fats[0]["value"] != 15.0, "Bug ×10 ainda presente!"
        assert fats[0]["value"] == 1.5
