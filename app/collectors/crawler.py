from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.collectors.http_client import HttpClient
from app.core.logging import logger
from app.parsers.html_parser import extract_guarantee_section


@dataclass(slots=True)
class CrawlResult:
    """
    Resultado da coleta de uma página de produto.
    """

    url: str
    success: bool

    html: str | None
    guarantee_section: str | None

    error: str | None = None


class CobasiCrawler:
    """
    Responsável por obter o HTML do produto
    e extrair a seção 'Níveis de Garantia'.
    """

    INVALID_PAGE_MARKERS = (
        "captcha",
        "cloudflare",
        "access denied",
        "forbidden",
        "temporarily unavailable",
    )

    def __init__(self) -> None:
        self.client = HttpClient()

    def collect(
        self,
        url: str,
    ) -> CrawlResult:
        """
        Coleta uma página de produto e extrai a seção
        de Níveis de Garantia.

        Parameters
        ----------
        url : str
            URL do produto.

        Returns
        -------
        CrawlResult
        """

        try:

            response = self.client.get(url)

            html = response.text

            if self._is_invalid_page(html):

                logger.warning(
                    "Página inválida detectada: %s",
                    url,
                )

                return CrawlResult(
                    url=url,
                    success=False,
                    html=None,
                    guarantee_section=None,
                    error="invalid_page",
                )

            guarantee = extract_guarantee_section(html)

            if guarantee is None:

                logger.debug(
                    "Níveis de garantia não encontrados: %s",
                    url,
                )

            logger.debug(
                "Produto processado com sucesso: %s",
                url,
            )

            return CrawlResult(
                url=url,
                success=True,
                html=html,
                guarantee_section=guarantee,
            )

        except httpx.HTTPError as exc:

            logger.warning(
                "Erro HTTP ao acessar %s: %s",
                url,
                exc,
            )

            return CrawlResult(
                url=url,
                success=False,
                html=None,
                guarantee_section=None,
                error=str(exc),
            )

        except Exception as exc:

            logger.exception(
                "Erro inesperado ao acessar %s",
                url,
            )

            return CrawlResult(
                url=url,
                success=False,
                html=None,
                guarantee_section=None,
                error=str(exc),
            )

    @classmethod
    def _is_invalid_page(
        cls,
        html: str,
    ) -> bool:
        """
        Verifica se o HTML retornado corresponde
        a uma página inválida.
        """

        html = html.lower()

        return any(
            marker in html
            for marker in cls.INVALID_PAGE_MARKERS
        )

    def close(self) -> None:
        """
        Fecha o cliente HTTP.
        """

        self.client.close()

    def __enter__(self) -> "CobasiCrawler":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()