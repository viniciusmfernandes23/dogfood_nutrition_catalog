"""
executar_pipeline.py — Ponto de entrada executável do pipeline de nutrição canina.

Após a refatoração (Sprint 1 do Roadmap), este arquivo atua como um
wrapper enxuto que delega toda a lógica para os serviços em
``app.services``.

Compatibilidade retroativa:
  - ``format_currency`` permanece importável (usada por testes).
  - ``_extract_sku_variations`` permanece importável (usada por testes).
  - ``run_extraction()`` permanece como função principal (usada por CLI).
"""

from __future__ import annotations

import argparse
import re
import sys
import os

import pandas as pd

# Garantir que o diretório do projeto está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------------------
# Funções de compatibilidade (usadas por testes existentes)
# ----------------------------------------------------------


_WEIGHT_PATTERN = re.compile(
    r"(?:(\d+(?:[.,]\d+)?)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g)\b",
    re.IGNORECASE,
)


def format_currency(value):
    """
    Formata valor para padrão de moeda brasileira amigável ao Power BI.

    Mantida aqui para compatibilidade com ``tests/test_currency_fix.py``.
    A implementação real vive em ``app.services.warehouse_post_processor``.
    """
    from app.services.warehouse_post_processor import format_currency as _fc
    return _fc(value)


def _parse_weight_kg(sku_name: str | None) -> float | None:
    """
    Extrai o peso em kg a partir do nome do SKU.

    Mantida aqui para compatibilidade retroativa.
    Delega para ``app.services._sku_parsers.cobasi_parse_weight``.
    """
    from app.services._sku_parsers import cobasi_parse_weight
    return cobasi_parse_weight(sku_name)


def _extract_sku_variations(
    api_payload: dict, marketplace: str = "Cobasi"
) -> list[dict]:
    """
    Extrai variações de SKU de um produto.

    Mantida aqui para compatibilidade com ``tests/test_petlove_integration.py``.
    Delega para o CollectorFactory.
    """
    from app.services.collector_factory import CollectorFactory

    factory = CollectorFactory()
    collector = factory.create(marketplace)
    return collector.extract_sku_variations(api_payload)


# ----------------------------------------------------------
# Função principal (wrapper enxuto)
# ----------------------------------------------------------


def run_extraction():
    """
    Ponto de entrada principal do pipeline.

    Interpreta argumentos de linha de comando e delega a execução
    ao ``PipelineRunner``.
    """
    from app.services.pipeline_runner import PipelineRunner

    parser = argparse.ArgumentParser(description="Pipeline de Nutrição Canina")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "price"],
        default="full",
        help="Modo: 'full' (atualiza tudo + crawler) ou 'price' (apenas preços)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Diretório de saída (padrão: output)",
    )
    parser.add_argument(
        "--marketplaces",
        type=str,
        nargs="+",
        default=["Cobasi"],
        help="Lista de marketplaces a coletar (padrão: Cobasi)",
    )
    args, _ = parser.parse_known_args()

    runner = PipelineRunner(
        output_dir=args.output_dir,
        mode=args.mode,
        marketplaces=args.marketplaces,
    )

    result = runner.run()

    if not result.get("success"):
        print(f"\nPipeline falhou: {result.get('error', result.get('reason', 'desconhecido'))}")
        sys.exit(1)

    # Resumo no console
    metrics = result.get("metrics", {})
    print(f"\n  Produtos coletados: {metrics.get('products_collected', 0)}")
    print(f"  Produtos normalizados: {metrics.get('products_normalized', 0)}")
    print(f"  Produtos exportados: {metrics.get('products_exported', 0)}")
    print(f"  Tempo total: {metrics.get('elapsed_seconds', 0):.1f}s")


# ----------------------------------------------------------
# Execução direta
# ----------------------------------------------------------


if __name__ == "__main__":
    run_extraction()
