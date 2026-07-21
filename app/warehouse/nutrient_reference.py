from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from app.normalization.rules import (
    NORMALIZATION_RULES,
    MACRONUTRIENTS,
    MINERALS,
    AMINO_ACIDS,
    FATTY_ACIDS,
    VITAMINS,
    ENERGY
)

@dataclass
class NutrientReference:
    nutrient_key: str
    category: str
    target_min: float | None
    target_max: float | None
    upper_safe_limit: float | None
    unit: str

class NutrientReferenceBuilder:
    """
    Constrói a dimensão de referência de nutrientes.
    """

    @staticmethod
    def build() -> pd.DataFrame:
        records = []
        
        for key, rule in NORMALIZATION_RULES.items():
            # Determina a categoria
            category = "Outros"
            if key in MACRONUTRIENTS: category = "Macronutrientes"
            elif key in MINERALS: category = "Microminerais"
            elif key in AMINO_ACIDS: category = "Aminoácidos"
            elif key in FATTY_ACIDS: category = "Ácidos Graxos"
            elif key in VITAMINS: category = "Vitaminas"
            elif key in ENERGY: category = "Energia"
            
            # Determina a unidade
            unit = "mg/kg"
            if key.endswith("_gkg"): unit = "g/kg"
            elif key.endswith("_kcalkg"): unit = "kcal/kg"
            elif key.endswith("_uikg"): unit = "UI/kg"
            
            # Limite superior seguro (exemplo: 1.5x o max para alguns minerais)
            # No futuro isso pode vir de uma tabela científica (AAFCO/FEDIAF)
            upper_safe_limit = rule.target_max * 1.5 if rule.target_max else None

            records.append({
                "nutrient_key": key,
                "category": category,
                "target_min": rule.target_min,
                "target_max": rule.target_max,
                "upper_safe_limit": upper_safe_limit,
                "unit": unit
            })
            
        return pd.DataFrame(records)

    @staticmethod
    def export_csv(dataframe: pd.DataFrame, output_path: str) -> None:
        dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
