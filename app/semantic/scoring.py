from __future__ import annotations
import pandas as pd
import numpy as np
from app.warehouse.nutrient_reference import NutrientReferenceBuilder

class NutritionalScoring:
    """
    Calcula indicadores nutricionais categorizados (Macro, Micro, Amino, Ácidos Graxos).
    """
    
    CATEGORIES = {
        "Macro": ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"],
        "Micro": [
            "calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg", "sodium_mgkg", 
            "potassium_mgkg", "magnesium_mgkg", "iron_mgkg", "zinc_mgkg", "selenium_mgkg",
            "vitamin_a_uikg", "vitamin_d3_uikg", "vitamin_e_uikg"
        ],
        "Amino": ["lysine_mgkg", "methionine_mgkg", "tryptophan_mgkg", "arginine_mgkg", "taurine_mgkg"],
        "Lipids": ["omega_3_mgkg", "omega_6_mgkg", "epa_dha_mgkg"]
    }

    def __init__(self):
        self.reference = NutrientReferenceBuilder.build()

    def calculate_scores(self, row: pd.Series) -> dict[str, float]:
        """
        Calcula um score de 0 a 100 para cada categoria baseado na presença e validade dos dados.
        """
        scores = {}
        
        for category, fields in self.CATEGORIES.items():
            present_count = 0
            valid_count = 0
            
            for field in fields:
                val = row.get(field)
                if pd.notna(val):
                    present_count += 1
                    # Verifica se o valor é plausível (não foi anulado pelo auditor)
                    # No warehouse longo, o status estaria na fact_nutrient, mas aqui no 
                    # DataFrame de enriquecimento, se o valor está presente, ele passou pela barreira.
                    valid_count += 1
            
            # Score baseado na densidade de informações nutricionais declaradas
            # Um produto com mais nutrientes informados e válidos ganha score maior na categoria
            score = (valid_count / len(fields)) * 100 if fields else 0
            scores[f"score_{category.lower()}"] = round(score, 2)
            
        return scores

    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona as colunas de score ao DataFrame."""
        df = df.copy()
        
        score_cols = [f"score_{cat.lower()}" for cat in self.CATEGORIES.keys()]
        for col in score_cols:
            df[col] = 0.0
            
        for index, row in df.iterrows():
            scores = self.calculate_scores(row)
            for col, val in scores.items():
                df.at[index, col] = val
                
        return df
