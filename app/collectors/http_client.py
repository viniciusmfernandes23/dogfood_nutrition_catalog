from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.core.logging import logger


class HttpClient:

    def __init__(self):

        self.client = httpx.Client(

            timeout=settings.timeout,

            follow_redirects=True,

            headers={

                "User-Agent":
                    (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64)"
                    ),

                "Accept":
                    "application/json,text/html",

            },

        )

    def get(
        self,
        url: str,
    ) -> httpx.Response:

        for attempt in range(settings.retries):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                # Se for erro de cliente (4xx), não adianta tentar de novo na maioria das vezes
                if 400 <= e.response.status_code < 500:
                    logger.error(f"Erro de Cliente {e.response.status_code} para URL: {url}")
                    raise
                
                logger.warning(f"Tentativa {attempt + 1}/{settings.retries} falhou com status {e.response.status_code}. Retentando...")
                if attempt == settings.retries - 1:
                    raise
                
                # Backoff exponencial com jitter
                wait_time = (2 ** attempt) + (time.time() % 1)
                time.sleep(wait_time)
            except httpx.HTTPError as e:
                logger.warning(f"Tentativa {attempt + 1}/{settings.retries} falhou com erro de rede: {e}. Retentando...")
                if attempt == settings.retries - 1:
                    raise
                
                wait_time = (2 ** attempt) + (time.time() % 1)
                time.sleep(wait_time)

        raise RuntimeError(
            "Falha inesperada."
        )

    def close(self):

        self.client.close()

    def __enter__(self):

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        self.close()