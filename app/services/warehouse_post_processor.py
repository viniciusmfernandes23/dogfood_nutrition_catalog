"""
WarehousePostProcessor — Pós-processamento da camada de warehouse.

Responsável por:
  - Formatação monetária (moeda brasileira para Power BI)
  - Sanitização de IDs
  - Remoção de colunas obsoletas
  - Aplicação de encoding correto nos CSVs

Esta classe consolida o pós-processamento que antes estava
espalhado no executar_pipeline.py, centralizando-o em um
serviço testável e reutilizável.
"""

from __future__ import annotations

import os

import pandas as pd
from app.core.logging import logger


def format_currency(value):
    """
    Formata valor para padrão de moeda brasileira amigável ao Power BI.

    Converte valores numéricos para string no formato "154,90" (pt-BR).
    Mantida como função de módulo para compatibilidade com testes
    existentes que importam diretamente de executar_pipeline.
    """
    if value is None or pd.isna(value):
        return None

    try:
        num_value = float(str(value).replace(",", "."))
        return f"{num_value:.2f}".replace(".", ",")
    except (ValueError, TypeError):
        return str(value)


class WarehousePostProcessor:
    """
    Aplica transformações de pós-processamento nos CSVs do warehouse.
    """

    # Colunas que devem receber formatação de moeda
    CURRENCY_PATTERNS = ("price",)

    # Colunas obsoletas a remover
    OBSOLETE_COLUMNS = ("gender",)

    def __init__(self, warehouse_dir: str) -> None:
        self._warehouse_dir = warehouse_dir

    def process_all(self) -> dict[str, str]:
        """
        Processa todos os CSVs do warehouse e retorna um dicionário
        {filename: status} com o resultado de cada arquivo.
        """
        files = [
            "dim_product.csv",
            "fact_nutrient.csv",
            "fact_price_snapshot.csv",
            "fact_product_review.csv",
            "sanity_audit_logs.csv",
        ]

        results = {}
        for filename in files:
            path = os.path.join(self._warehouse_dir, filename)
            if not os.path.exists(path):
                continue

            try:
                self._process_file(path, filename)
                results[filename] = "ok"
                logger.info("  Pós-processamento OK: %s", filename)
            except Exception as exc:
                results[filename] = f"error: {exc}"
                logger.error("  ERRO no pós-processamento de %s: %s", filename, exc)

        return results

    def _process_file(self, path: str, filename: str) -> None:
        """Aplica as transformações em um único arquivo CSV."""
        df = pd.read_csv(path)

        # Sanitização de IDs vazios
        if "product_id" in df.columns:
            df = df.dropna(subset=["product_id"])
            df = df[df["product_id"].astype(str).str.strip() != ""]

        # Remoção de colunas obsoletas
        cols_to_drop = [c for c in self.OBSOLETE_COLUMNS if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        # Formatação monetária
        currency_cols = [c for c in df.columns if "price" in c.lower()]
        for col in currency_cols:
            df[col] = df[col].apply(format_currency)

        # Reexportação com encoding correto
        df.to_csv(path, index=False, encoding="utf-8-sig")
