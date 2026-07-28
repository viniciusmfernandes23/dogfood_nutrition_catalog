"""
PipelineSummaryReporter — Relatório consolidado de métricas do pipeline.

Gera um resumo textual formatado com as métricas operacionais
completas, seguindo o layout sugerido no roadmap:

    ======================================
    Pipeline Summary
    Collection          1.243 produtos
    Crawler             Tempo: 2m12s
    Parser              98,7% sucesso
    Normalization       126 correções
    Warehouse           4 arquivos exportados
    Tempo total         2m47s
    ======================================
"""

from __future__ import annotations

from typing import Any

from app.pipeline.models import PipelineMetrics


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para string legível (ex: '2m12s').
    """
    if seconds < 0:
        return "0s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}m{secs}s"
    return f"{secs}s"


class PipelineSummaryReporter:
    """
    Gera relatório textual consolidado a partir de PipelineMetrics.
    """

    SEPARATOR = "=" * 42

    def __init__(self, metrics: PipelineMetrics | None = None) -> None:
        self.metrics = metrics

    def generate(self) -> str:
        """Gera o relatório textual completo."""
        if self.metrics is None:
            return "Sem métricas disponíveis."

        m = self.metrics
        lines = [
            self.SEPARATOR,
            "",
            "Pipeline Summary",
            "",
            self._collection_section(m),
            self._crawler_section(m),
            self._parser_section(m),
            self._normalization_section(m),
            self._warehouse_section(m),
            self._pipeline_section(m),
            "",
            self.SEPARATOR,
        ]
        return "\n".join(lines)

    def print(self) -> None:
        """Imprime o relatório no console."""
        print(self.generate())

    def to_dict(self) -> dict[str, Any]:
        """Retorna o relatório como dicionário estruturado."""
        m = self.metrics
        return {
            "collection": {
                "products": m.products_collected,
            },
            "crawler": {
                "found": getattr(m, "crawler_products_found", 0),
                "processed": getattr(m, "crawler_products_processed", 0),
                "discarded": getattr(m, "crawler_products_discarded", 0),
                "total_time": format_duration(getattr(m, "crawler_total_time_seconds", 0)),
                "avg_per_product": getattr(m, "crawler_avg_time_per_product_seconds", 0),
                "success_rate": getattr(m, "crawler_success_rate", 0),
            },
            "parser": {
                "nutrients_found": getattr(m, "parser_nutrients_found", 0),
                "nutrients_missing": getattr(m, "parser_nutrients_missing", 0),
                "success_rate": getattr(m, "parser_success_rate", 0),
            },
            "normalization": {
                "changes": m.normalization_changes,
                "rules_applied": getattr(m, "normalization_rules_applied", 0),
                "discarded": getattr(m, "normalization_discarded", 0),
            },
            "warehouse": {
                "files_exported": getattr(m, "warehouse_files_exported", 0),
                "records_exported": getattr(m, "warehouse_records_exported", 0),
            },
            "pipeline": {
                "total_time": format_duration(m.elapsed_seconds),
                "throughput": getattr(m, "pipeline_throughput_products_per_second", 0),
            },
        }

    # ----------------------------------------------------------
    # Seções do relatório
    # ----------------------------------------------------------

    def _collection_section(self, m: PipelineMetrics) -> str:
        return (
            f"Collection\n"
            f"  {m.products_collected:,} produtos"
        )

    def _crawler_section(self, m: PipelineMetrics) -> str:
        total_time = getattr(m, "crawler_total_time_seconds", 0)
        success_rate = getattr(m, "crawler_success_rate", 0)
        return (
            f"Crawler\n"
            f"  Tempo: {format_duration(total_time)}\n"
            f"  Sucesso: {success_rate}%\n"
            f"  Processados: {m.crawler_products_processed:,}\n"
            f"  Descartados: {m.crawler_products_discarded:,}"
        )

    def _parser_section(self, m: PipelineMetrics) -> str:
        success_rate = getattr(m, "parser_success_rate", 0)
        return (
            f"Parser\n"
            f"  {success_rate}% sucesso\n"
            f"  Nutrientes encontrados: {m.parser_nutrients_found:,}\n"
            f"  Nutrientes ausentes: {m.parser_nutrients_missing:,}"
        )

    def _normalization_section(self, m: PipelineMetrics) -> str:
        rules_applied = getattr(m, "normalization_rules_applied", 0)
        discarded = getattr(m, "normalization_discarded", 0)
        return (
            f"Normalization\n"
            f"  {m.normalization_changes} correções\n"
            f"  Regras aplicadas: {rules_applied}\n"
            f"  Descartados: {discarded}"
        )

    def _warehouse_section(self, m: PipelineMetrics) -> str:
        files = getattr(m, "warehouse_files_exported", 0)
        records = getattr(m, "warehouse_records_exported", 0)
        return (
            f"Warehouse\n"
            f"  {files} arquivos exportados\n"
            f"  {records:,} registros exportados"
        )

    def _pipeline_section(self, m: PipelineMetrics) -> str:
        throughput = getattr(m, "pipeline_throughput_products_per_second", 0)
        return (
            f"Pipeline\n"
            f"  Tempo total: {format_duration(m.elapsed_seconds)}\n"
            f"  Throughput: {throughput} produtos/s"
        )
