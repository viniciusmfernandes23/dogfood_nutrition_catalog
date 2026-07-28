"""
NutritionExtractionService — Serviço de extração nutricional.

Responsável por:
  1. Executar o crawler para obter o HTML da seção de garantia.
  2. Fazer o parse nutricional.
  3. Mapear nutrientes para colunas canônicas.
  4. Selecionar o melhor match por prioridade.
  5. Reportar métricas ao PipelineMetricsCollector.
"""

from __future__ import annotations

import pandas as pd

from app.core.logging import logger
from app.normalization.rules import NORMALIZATION_RULES
from app.parsers.nutrition_parser import parse_nutrition


# Sufixos de unidade usados pelos campos canônicos de normalização.
# A remoção do sufixo — e não a divisão no primeiro "_" — preserva chaves
# compostas, como ``calcium_min``, ``l_carnitine`` e ``metabolizable_energy``.
_UNIT_SUFFIXES = ("_kcalkg", "_uikg", "_mgkg", "_gkg")


def _nutrient_key_from_rule(rule_key: str) -> str:
    """Converte um campo canônico da normalização na chave emitida pelo parser."""
    for suffix in _UNIT_SUFFIXES:
        if rule_key.endswith(suffix):
            return rule_key[: -len(suffix)]
    return rule_key


# Mapeamento completo de nutrientes → colunas canônicas do DataFrame.
# A fonte única de verdade é NORMALIZATION_RULES: assim, toda regra adicionada
# ao motor passa automaticamente a ser elegível para extração e persistência.
NUTRIENT_MAPPING: dict[str, str] = {
    _nutrient_key_from_rule(rule_key): rule_key
    for rule_key in NORMALIZATION_RULES
}

# Nutrientes esperados (referência para métricas)
EXPECTED_NUTRIENTS = set(NUTRIENT_MAPPING.keys())


class NutritionExtractionService:
    """
    Extrai nutrientes dos dados brutos de garantia e os mapeia
    para colunas canônicas no DataFrame.
    """

    def __init__(self) -> None:
        pass

    def extract_and_map(
        self,
        dataframe: pd.DataFrame,
        guarantee_column: str = "raw_guarantee",
        metrics_collector: object | None = None,
    ) -> pd.DataFrame:
        """
        Para cada linha do DataFrame, faz o parse da coluna de garantia
        e escreve os nutrientes nas colunas canônicas.

        Retorna o DataFrame modificado com as colunas de nutrientes preenchidas.
        """
        logger.info(
            "Processando %d produtos para extração de nutrientes...",
            len(dataframe),
        )

        nutrient_cols = list(NUTRIENT_MAPPING.values())

        # Garante que as colunas canônicas existam
        for col in nutrient_cols:
            if col not in dataframe.columns:
                dataframe[col] = None
            unit_col = f"{col}_unit"
            if unit_col not in dataframe.columns:
                dataframe[unit_col] = None

        # Contadores para métricas de integridade entre parser e normalização.
        total_nutrients_parsed = 0
        total_nutrients_found = 0
        total_nutrients_missing = 0
        products_with_nutrients = 0

        for index, row in dataframe.iterrows():
            raw_guarantee = row.get(guarantee_column)
            if not raw_guarantee or (isinstance(raw_guarantee, float) and pd.isna(raw_guarantee)):
                total_nutrients_missing += len(EXPECTED_NUTRIENTS)
                continue

            nutrients = parse_nutrition(raw_guarantee)
            total_nutrients_parsed += len(nutrients)
            logger.info(
                "  Nutrientes brutos para %s: %d",
                row.get("product_name", "?"),
                len(nutrients),
            )

            best_matches = self._select_best(nutrients)

            if best_matches:
                products_with_nutrients += 1

            for target_col, data in best_matches.items():
                dataframe.at[index, target_col] = data["value"]
                unit_col = f"{target_col}_unit"
                dataframe.at[index, unit_col] = data.get("unit")
                total_nutrients_found += 1

            # Conta nutrientes esperados que não foram extraídos/mapeados.
            found_keys = {
                match["nutrient"]
                for match in best_matches.values()
                if "nutrient" in match
            }
            total_nutrients_missing += len(EXPECTED_NUTRIENTS - found_keys)

        # Reportar métricas
        if metrics_collector and hasattr(metrics_collector, "metrics"):
            m = metrics_collector.metrics
            # ``parser_nutrients_found`` é mantido como alias histórico de
            # ``parser_nutrients_mapped`` para não quebrar consumidores atuais.
            m.parser_nutrients_parsed = total_nutrients_parsed
            m.parser_nutrients_mapped = total_nutrients_found
            m.parser_nutrients_found = total_nutrients_found
            m.parser_products_with_nutrients = products_with_nutrients
            m.parser_nutrients_missing = total_nutrients_missing
            total_expected = len(dataframe) * len(EXPECTED_NUTRIENTS)
            if total_expected > 0:
                m.parser_success_rate = round(
                    (total_nutrients_found / total_expected) * 100, 1
                )

        success_rate = (
            round((products_with_nutrients / len(dataframe)) * 100, 1)
            if len(dataframe) > 0
            else 0
        )
        logger.info(
            "  Extração concluída: %d/%d produtos com nutrientes (%.1f%%), "
            "%d nutrientes parseados e %d mapeados",
            products_with_nutrients,
            len(dataframe),
            success_rate,
            total_nutrients_parsed,
            total_nutrients_found,
        )

        return dataframe

    def _select_best(
        self, nutrients: dict
    ) -> dict[str, dict]:
        """
        Seleciona o melhor match para cada nutriente canônico,
        priorizando valores com 'mín' ou 'máx' no alias.
        """
        best_matches: dict[str, dict] = {}

        for _nut_key, nut_data in nutrients.items():
            nut_type = nut_data["nutrient"]
            target_col = NUTRIENT_MAPPING.get(nut_type)
            if not target_col:
                continue

            alias = nut_data.get("matched_alias", "").lower()
            priority = 2 if any(x in alias for x in ["mín", "min", "máx", "max"]) else 1

            if (
                target_col not in best_matches
                or priority > best_matches[target_col]["priority"]
            ):
                best_matches[target_col] = {
                    "value": nut_data["value"],
                    "unit": nut_data.get("unit"),
                    "priority": priority,
                    "nutrient": nut_type,
                }

        return best_matches
