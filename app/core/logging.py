"""
Logging estruturado com structlog.

Compatível com o módulo ``logging`` da biblioteca padrão, mas emite
logs em formato estruturado (JSON) que facilita:
  - Rastreamento de falhas
  - Integração com plataformas de observabilidade
  - Filtragem por serviço
  - Métricas por execução

Exemplo de saída:
    {"service": "CrawlerService", "marketplace": "Cobasi",
     "product_id": 12345, "status": "success", "duration_ms": 182}

Para compatibilidade retroativa, o módulo ``logger`` continua sendo
um objeto ``logging.Logger`` que aceita ``.info()``, ``.warning()``,
``.error()``, ``.debug()`` com a mesma API de antes.
"""

from __future__ import annotations

import logging
import sys

import structlog

# ----------------------------------------------------------
# Configuração base do logging padrão
# ----------------------------------------------------------

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

# ----------------------------------------------------------
# Configuração do structlog
# ----------------------------------------------------------

structlog.configure(
    processors=[
        # Adiciona contexto global (timestamp, nivel)
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        # Processa exceções em formato estruturado
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Serializa para JSON em produção
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str = "dogfood_pipeline") -> structlog.stdlib.BoundLogger:
    """
    Retorna um logger estruturado vinculado ao nome informado.

    Uso:
        logger = get_logger("CrawlerService")
        logger.info("Crawling produto", product_id=12345, marketplace="Cobasi")
    """
    return structlog.get_logger(name)


def get_pipeline_logger(name: str = "dogfood_pipeline") -> structlog.stdlib.BoundLogger:
    """Alias para compatibilidade — retorna o logger principal."""
    return get_logger(name)


# ----------------------------------------------------------
# Compatibilidade retroativa: mantém ``logger`` como módulo global
# ----------------------------------------------------------

# Para código legado que faz ``from app.core.logging import logger``,
# expomos um logger estruturado global. Ele aceita os métodos padrão
# (.info, .warning, .error, .debug) com kwargs opcionais.
logger = structlog.get_logger("dogfood_pipeline")
