"""
Testes específicos para a captura de múltiplas variações de preço por produto.

Valida o comportamento do PriceSnapshotFactBuilder quando o DataFrame contém
o campo ``sku_variations`` com múltiplas embalagens/tamanhos por produto,
refletindo a estrutura real da API VTEX da Cobasi.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.warehouse.fact_price_snapshot import (
    PriceSnapshotFactBuilder,
    _parse_weight_kg,
)
from app.warehouse.exporter import WarehouseExporter


# ==========================================================
# Fixtures
# ==========================================================


def make_product_with_variations(
    product_id: int = 3853925,
    product_name: str = "Ração GranPlus Choice Frango e Carne Cães Adultos",
    variations: list[dict] | None = None,
) -> pd.DataFrame:
    """
    Cria um DataFrame simulando o payload de um produto com múltiplas
    variações de embalagem, como retornado pela API VTEX da Cobasi.
    """
    if variations is None:
        variations = [
            {
                "sku_id": "915700",
                "sku_name": "GranPlus Choice Frango e Carne 10,1kg",
                "package_weight_kg": 10.1,
                "price": 189.90,
                "list_price": 209.90,
                "subscriber_price": 170.91,
                "price_per_kg": 18.80,
                "available": True,
            },
            {
                "sku_id": "915701",
                "sku_name": "GranPlus Choice Frango e Carne 15kg",
                "package_weight_kg": 15.0,
                "price": 259.90,
                "list_price": 289.90,
                "subscriber_price": 233.91,
                "price_per_kg": 17.33,
                "available": True,
            },
            {
                "sku_id": "915702",
                "sku_name": "GranPlus Choice Frango e Carne 20kg",
                "package_weight_kg": 20.0,
                "price": 329.90,
                "list_price": 369.90,
                "subscriber_price": 296.91,
                "price_per_kg": 16.50,
                "available": False,
            },
        ]

    return pd.DataFrame([{
        "product_id": product_id,
        "product_name": product_name,
        "brand": "GranPlus",
        "price": variations[0]["price"],  # Valor representativo (primeira variação)
        "available": any(v.get("available", False) for v in variations),
        "sku_variations": variations,
    }])


# ==========================================================
# Testes: _parse_weight_kg
# ==========================================================


class TestParseWeightKg:
    """Testa a extração de peso a partir do nome do SKU."""

    def test_parse_kg_integer(self):
        assert _parse_weight_kg("Ração 15kg") == 15.0

    def test_parse_kg_decimal_comma(self):
        assert _parse_weight_kg("GranPlus 10,1kg") == 10.1

    def test_parse_kg_decimal_dot(self):
        assert _parse_weight_kg("Premier 1.5 kg") == 1.5

    def test_parse_grams_to_kg(self):
        assert _parse_weight_kg("Petisco 500g") == 0.5

    def test_parse_multiplier(self):
        assert _parse_weight_kg("Kit 2x15kg") == 30.0

    def test_parse_no_weight(self):
        assert _parse_weight_kg("Ração Super Premium") is None

    def test_parse_none(self):
        assert _parse_weight_kg(None) is None

    def test_parse_empty_string(self):
        assert _parse_weight_kg("") is None


# ==========================================================
# Testes: PriceSnapshotFactBuilder — modo multi-variação
# ==========================================================


class TestPriceSnapshotMultiVariation:
    """Testa a expansão de múltiplas variações de SKU em linhas separadas."""

    def test_expands_variations_into_multiple_rows(self):
        """Produto com 3 variações deve gerar 3 linhas no fact."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert len(fact) == 3

    def test_each_row_has_distinct_sku_id(self):
        """Cada linha deve ter um sku_id distinto."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert fact["sku_id"].nunique() == 3

    def test_product_id_is_same_for_all_rows(self):
        """Todas as linhas devem referenciar o mesmo product_id."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert (fact["product_id"] == 3853925).all()

    def test_prices_differ_across_variations(self):
        """Preços devem ser distintos entre variações de embalagem."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert fact["price"].nunique() == 3

    def test_price_per_kg_decreases_with_larger_package(self):
        """Embalagens maiores devem ter menor preço por kg (economia de escala)."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        # Ordena por peso para verificar a tendência
        fact_sorted = fact.sort_values("package_weight_kg").reset_index(drop=True)
        prices_per_kg = fact_sorted["price_per_kg"].tolist()
        assert prices_per_kg[0] > prices_per_kg[-1], (
            "Embalagem menor deve ter maior preço/kg que embalagem maior"
        )

    def test_required_columns_present(self):
        """Verifica que todas as colunas obrigatórias estão presentes."""
        required = [
            "product_id", "sku_id", "sku_name", "package_weight_kg",
            "price", "list_price", "subscriber_price", "price_per_kg",
            "available", "collected_at",
            "has_price", "has_price_per_kg", "has_subscriber_price",
        ]
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        for col in required:
            assert col in fact.columns, f"Coluna obrigatória ausente: {col}"

    def test_availability_per_variation(self):
        """Variações indisponíveis devem ter available=False."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        # A terceira variação (20kg) está indisponível
        row_20kg = fact[fact["sku_id"] == "915702"].iloc[0]
        assert row_20kg["available"] is False or row_20kg["available"] == False

    def test_list_price_greater_than_price(self):
        """Preço de lista deve ser maior ou igual ao preço de venda."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert (fact["list_price"] >= fact["price"]).all()

    def test_subscriber_price_less_than_price(self):
        """Preço de assinante deve ser menor que o preço de venda."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert (fact["subscriber_price"] < fact["price"]).all()


# ==========================================================
# Testes: PriceSnapshotFactBuilder — modo retrocompatível
# ==========================================================


class TestPriceSnapshotScalarCompatibility:
    """Testa compatibilidade retroativa com DataFrames sem sku_variations."""

    def test_scalar_mode_generates_one_row(self):
        """Produto sem sku_variations deve gerar exatamente 1 linha."""
        df = pd.DataFrame([{
            "product_id": 1,
            "sku": "SKU001",
            "price": 249.90,
            "in_stock": True,
        }])
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        assert len(fact) == 1

    def test_scalar_mode_calculates_price_per_kg_from_sku_name(self):
        """Deve calcular price_per_kg quando o peso está no nome do SKU."""
        df = pd.DataFrame([{
            "product_id": 1,
            "sku": "Ração Premier 15kg",
            "price": 249.90,
            "in_stock": True,
        }])
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)
        expected = round(249.90 / 15.0, 4)
        assert fact.iloc[0]["price_per_kg"] == pytest.approx(expected, rel=1e-3)


# ==========================================================
# Testes: Exportação e deduplicação incremental
# ==========================================================


class TestPriceSnapshotExport:
    """Testa a exportação e deduplicação do fact_price_snapshot com multi-variação."""

    def test_export_generates_correct_row_count(self, tmp_path: Path):
        """CSV exportado deve conter uma linha por variação de SKU."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)

        exporter = WarehouseExporter(output_dir=tmp_path)
        path = exporter.export_fact(fact, "fact_price_snapshot.csv")

        exported = pd.read_csv(path, encoding="utf-8-sig")
        assert len(exported) == 3

    def test_incremental_append_preserves_all_variations(self, tmp_path: Path):
        """
        Ao re-executar o pipeline no mesmo dia, variações distintas do mesmo
        produto não devem ser colapsadas em uma única linha.
        """
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)

        exporter = WarehouseExporter(output_dir=tmp_path)
        # Primeira exportação
        exporter.export_fact(fact, "fact_price_snapshot.csv")
        # Segunda exportação (simula re-execução no mesmo dia)
        path = exporter.export_fact(fact, "fact_price_snapshot.csv")

        exported = pd.read_csv(path, encoding="utf-8-sig")
        # Deve manter 3 linhas (uma por variação), não duplicar
        assert len(exported) == 3

    def test_csv_contains_required_columns(self, tmp_path: Path):
        """CSV exportado deve conter todas as colunas do novo schema."""
        df = make_product_with_variations()
        builder = PriceSnapshotFactBuilder()
        fact = builder.build(df)

        exporter = WarehouseExporter(output_dir=tmp_path)
        path = exporter.export_fact(fact, "fact_price_snapshot.csv")

        exported = pd.read_csv(path, encoding="utf-8-sig")
        required_cols = [
            "product_id", "sku_id", "sku_name", "package_weight_kg",
            "price", "list_price", "price_per_kg", "available", "collected_at",
        ]
        for col in required_cols:
            assert col in exported.columns, f"Coluna ausente no CSV: {col}"
