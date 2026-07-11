from __future__ import annotations

import pandas as pd
from app.normalization.metadata import get_nutrient_metadata


class SemanticLayer:
    """
    Responsável por transformar os dados da representação técnica interna
    para a representação semântica de negócio baseada em metadados.
    """

    @staticmethod
    def apply_output_conversion(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica as conversões de escala definidas nos metadados para cada nutriente.
        Espera um DataFrame no formato fact_nutrient (colunas nutrient_name e nutrient_value).
        """
        if df is None or df.empty or "nutrient_name" not in df.columns or "nutrient_value" not in df.columns:
            return df

        # Copia para evitar efeitos colaterais
        df = df.copy()

        # Identifica os nutrientes únicos presentes no DataFrame
        nutrients = df["nutrient_name"].unique()

        for nutrient in nutrients:
            metadata = get_nutrient_metadata(nutrient)
            if metadata and metadata.output_scale_factor != 1.0:
                mask = df["nutrient_name"] == nutrient
                # Aplica o fator de escala de saída
                df.loc[mask, "nutrient_value"] = (df.loc[mask, "nutrient_value"] * metadata.output_scale_factor).round(2)

        return df
