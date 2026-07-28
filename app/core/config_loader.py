"""
ConfigLoader — Carrega configuração externa do config/config.yaml.

Suporta:
  - Leitura de config.yaml com valores padrão embutidos
  - Sobrescrita por variáveis de ambiente (.env)
  - Sobrescrita por argumentos de linha de comando
  - Fallback para valores hard-coded caso o YAML não exista

Uso:
    config = ConfigLoader.load()
    max_workers = config.crawler.max_workers
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.logging import logger


# Caminho padrão do config.yaml relativo à raiz do projeto
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.yaml"


@dataclass(slots=True)
class CrawlerConfig:
    max_workers: int = 12
    timeout: int = 15
    retries: int = 5
    request_delay: float = 0.3
    progress_step: int = 20


@dataclass(slots=True)
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"
    log_file: str = ""


@dataclass(slots=True)
class CollectorEndpointConfig:
    endpoint: str = ""
    page_size: int = 50
    default_queries: list[str] = field(default_factory=list)
    base_url: str = ""


@dataclass(slots=True)
class CollectorsConfig:
    cobasi: CollectorEndpointConfig = field(default_factory=CollectorEndpointConfig)
    petlove: CollectorEndpointConfig = field(default_factory=CollectorEndpointConfig)
    petz: CollectorEndpointConfig = field(default_factory=CollectorEndpointConfig)


@dataclass(slots=True)
class PipelineConfig:
    """
    Configuração completa do pipeline, carregada do config.yaml.
    """

    output_dir: str = "output"
    warehouse_dir: str = "output/warehouse"
    default_mode: str = "full"
    overwrite: bool = True
    export_csv: bool = True
    save_logs: bool = True

    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    collectors: CollectorsConfig = field(default_factory=CollectorsConfig)


class ConfigLoader:
    """
    Carrega configuração do YAML com fallback para defaults.

    Uso:
        config = ConfigLoader.load()
        print(config.crawler.max_workers)
    """

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """
        Carrega a configuração do arquivo YAML.

        Se o arquivo não existir, retorna uma instância com valores padrão.
        """
        config_path = Path(path) if path else _DEFAULT_CONFIG_PATH

        if not config_path.exists():
            logger.warning(
                "Config file not found at %s; using defaults.",
                config_path,
            )
            return cls._apply_env_overrides(PipelineConfig())

        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed; using defaults.")
            return cls._apply_env_overrides(PipelineConfig())

        with open(config_path, "r", encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f)

        if not isinstance(raw, dict):
            logger.warning("Invalid config.yaml format; using defaults.")
            return cls._apply_env_overrides(PipelineConfig())

        config = PipelineConfig()

        # Pipeline
        p = raw.get("pipeline", {})
        if p:
            config.output_dir = p.get("output_dir", config.output_dir)
            config.warehouse_dir = p.get("warehouse_dir", config.warehouse_dir)
            config.default_mode = p.get("default_mode", config.default_mode)
            config.overwrite = p.get("overwrite", config.overwrite)
            config.export_csv = p.get("export_csv", config.export_csv)
            config.save_logs = p.get("save_logs", config.save_logs)

        # Crawler
        c = raw.get("crawler", {})
        if c:
            config.crawler = CrawlerConfig(
                max_workers=c.get("max_workers", config.crawler.max_workers),
                timeout=c.get("timeout", config.crawler.timeout),
                retries=c.get("retries", config.crawler.retries),
                request_delay=c.get("request_delay", config.crawler.request_delay),
                progress_step=c.get("progress_step", config.crawler.progress_step),
            )

        # Logging
        log_cfg = raw.get("logging", {})
        if log_cfg:
            config.logging = LoggingConfig(
                level=log_cfg.get("level", config.logging.level),
                format=log_cfg.get("format", config.logging.format),
                log_file=log_cfg.get("log_file", config.logging.log_file),
            )

        # Collectors
        col = raw.get("collectors", {})
        if col:
            cobasi = col.get("cobasi", {})
            petlove = col.get("petlove", {})
            petz = col.get("petz", {})
            config.collectors = CollectorsConfig(
                cobasi=CollectorEndpointConfig(
                    endpoint=cobasi.get("endpoint", ""),
                    page_size=cobasi.get("page_size", 50),
                    default_queries=cobasi.get("default_queries", ["ração cachorro"]),
                ),
                petlove=CollectorEndpointConfig(
                    base_url=petlove.get("base_url", "https://www.petlove.com.br"),
                    default_queries=petlove.get(
                        "default_queries",
                        [
                            "ração cachorro premium",
                            "ração cachorro adulto",
                            "ração cachorro filhote",
                        ],
                    ),
                ),
                petz=CollectorEndpointConfig(
                    endpoint=petz.get("endpoint", ""),
                    default_queries=petz.get("default_queries", []),
                ),
            )

        # Aplica sobrescrita por variáveis de ambiente
        config = cls._apply_env_overrides(config)

        return config

    @classmethod
    def _apply_env_overrides(cls, config: PipelineConfig) -> PipelineConfig:
        """
        Aplica sobrescrita por variáveis de ambiente.

        Convenção: NOME_DA_SECAO__NOME_DO_CAMPO
        Ex: CRAWLER__MAX_WORKERS=8 sobrescreve config.crawler.max_workers
        """
        # Crawler overrides
        max_workers_env = os.environ.get("CRAWLER__MAX_WORKERS")
        if max_workers_env:
            try:
                config.crawler.max_workers = int(max_workers_env)
            except ValueError:
                pass

        timeout_env = os.environ.get("CRAWLER__TIMEOUT")
        if timeout_env:
            try:
                config.crawler.timeout = int(timeout_env)
            except ValueError:
                pass

        # Logging override
        log_level = os.environ.get("LOGGING__LEVEL")
        if log_level:
            config.logging.level = log_level

        # Output dir override
        output_dir_env = os.environ.get("PIPELINE__OUTPUT_DIR")
        if output_dir_env:
            config.output_dir = output_dir_env

        return config
