from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from app.warehouse.models import PriceSnapshotFact


# Padrão para extrair peso em kg a partir do nome do SKU.
# Exemplos reconhecidos: "15kg", "10,1 kg", "1.5kg", "500g", "2x15kg"
_WEIGHT_PATTERN = re.compile(
    r"(?:(\d+(?:[.,]\d+)?)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g)\b",
    re.IGNORECASE,
)


def _parse_weight_kg(sku_name: str | None) -> float | None:
    """
    Extrai o peso em kg a partir do nome do SKU.

    Suporta formatos como "15kg", "10,1 kg", "500g", "2x15kg".
    Retorna None quando não é possível determinar o peso.
    """
    if not sku_name:
        return None

    match = _WEIGHT_PATTERN.search(sku_name)
    if not match:
        return None

    multiplier_str, value_str, unit = match.groups()

    # Normaliza separador decimal (vírgula → ponto)
    value = float(value_str.replace(",", "."))

    if unit.lower() == "g":
        value = value / 1000.0

    if multiplier_str:
        multiplier = float(multiplier_str.replace(",", "."))
        value = multiplier * value

    return round(value, 4)


class PriceSnapshotFactBuilder:
    """
    Constrói a tabela fato de preços com suporte a múltiplas variações por produto.

    Cada linha do DataFrame de entrada pode conter uma lista de SKUs no campo
    ``sku_variations`` (gerado pelo extrator de payload da API VTEX) ou campos
    escalares de preço para compatibilidade retroativa.

    Quando ``sku_variations`` está presente, o builder expande cada variação em
    uma linha separada, permitindo rastrear o preço de cada embalagem/tamanho
    individualmente — essencial para rações disponíveis em múltiplos pesos.
    """

    def __init__(
        self,
        timestamp: datetime | None = None,
    ) -> None:

        self.timestamp = timestamp or datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if dataframe.empty:
            return pd.DataFrame()

        records: list[dict] = []

        for row in dataframe.to_dict(orient="records"):

            sku_variations: list[dict] | None = row.get("sku_variations")

            if sku_variations:
                # Modo multi-variação: expande cada SKU em uma linha separada
                for variation in sku_variations:
                    records.append(
                        self._build_from_variation(
                            product_id=row.get("product_id"),
                            variation=variation,
                        )
                    )
            else:
                # Modo retrocompatível: uma linha por produto com campos escalares
                records.append(
                    self._build_from_scalar(row)
                )

        fact_df = pd.DataFrame(records)

        # Colunas de flag para facilitar análises no Power BI
        fact_df["has_price"] = fact_df["price"].notna()
        fact_df["has_price_per_kg"] = fact_df["price_per_kg"].notna()
        fact_df["has_subscriber_price"] = fact_df["subscriber_price"].notna()

        return self._sort(fact_df)

    # ----------------------------------------------------------
    # Construtores internos
    # ----------------------------------------------------------

    def _build_from_variation(
        self,
        product_id: int | None,
        variation: dict,
    ) -> dict:
        """
        Constrói um registro de preço a partir de uma variação de SKU extraída
        diretamente do payload da API VTEX (campo ``sku_variations``).
        """
        sku_name = variation.get("sku_name")
        price = variation.get("price")
        list_price = variation.get("list_price")
        package_weight_kg = variation.get("package_weight_kg") or _parse_weight_kg(sku_name)

        price_per_kg: float | None = None
        if price is not None and package_weight_kg and package_weight_kg > 0:
            price_per_kg = round(price / package_weight_kg, 4)

        fact = PriceSnapshotFact(
            product_id=product_id,
            marketplace=variation.get("marketplace") or "Cobasi",
            ean=variation.get("ean"),
            sku_id=str(variation.get("sku_id")) if variation.get("sku_id") is not None else None,
            sku_name=sku_name,
            package_weight_kg=package_weight_kg,
            price=price,
            list_price=list_price,
            subscriber_price=variation.get("subscriber_price"),
            price_per_kg=price_per_kg,
            available=variation.get("available"),
            collected_at=self.timestamp,
        )

        return fact.to_dict()

    def _build_from_scalar(self, row: dict) -> dict:
        """
        Constrói um registro de preço a partir de campos escalares do DataFrame
        (compatibilidade com o formato anterior ao suporte multi-variação).
        """
        price = row.get("price")
        package_weight_kg: float | None = row.get("package_weight_kg") or row.get("package_size")
        sku_name: str | None = row.get("sku") or row.get("sku_name")

        # Tenta inferir peso do nome do SKU se não vier explícito
        if package_weight_kg is None:
            package_weight_kg = _parse_weight_kg(sku_name)

        # Calcula price_per_kg se não vier explícito
        price_per_kg: float | None = row.get("price_per_kg")
        if price_per_kg is None and price is not None and package_weight_kg and package_weight_kg > 0:
            price_per_kg = round(price / package_weight_kg, 4)

        fact = PriceSnapshotFact(
            product_id=row.get("product_id"),
            marketplace=row.get("marketplace") or "Cobasi",
            ean=row.get("ean"),
            sku_id=str(row.get("sku")) if row.get("sku") is not None else None,
            sku_name=sku_name,
            package_weight_kg=package_weight_kg,
            price=price,
            list_price=row.get("list_price"),
            subscriber_price=row.get("subscriber_price"),
            price_per_kg=price_per_kg,
            available=row.get("available") if row.get("available") is not None else row.get("in_stock"),
            collected_at=self.timestamp,
        )

        return fact.to_dict()

    # ----------------------------------------------------------
    # Ordenação
    # ----------------------------------------------------------

    @staticmethod
    def _sort(dataframe: pd.DataFrame) -> pd.DataFrame:

        if dataframe.empty:
            return dataframe

        sort_cols = [c for c in ("product_id", "sku_id") if c in dataframe.columns]

        if sort_cols:
            dataframe = dataframe.sort_values(by=sort_cols)

        return dataframe.reset_index(drop=True)

    # ----------------------------------------------------------
    # Exportação
    # ----------------------------------------------------------

    @staticmethod
    def export_csv(
        dataframe: pd.DataFrame,
        output_path: str,
    ) -> None:

        dataframe.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )
