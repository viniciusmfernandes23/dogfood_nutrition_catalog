from __future__ import annotations

import time
import random
import httpx

from app.core.config import settings
from app.core.logging import logger


class HttpClient:

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        self.client = httpx.Client(
            timeout=settings.timeout,
            follow_redirects=True,
        )

    def _get_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
        }

    def get(
        self,
        url: str,
    ) -> httpx.Response:

        for attempt in range(settings.retries):
            # Adiciona um jitter aleatório para parecer mais humano
            if attempt > 0:
                time.sleep(random.uniform(1.0, 3.0))
            
            try:
                response = self.client.get(url, headers=self._get_headers())
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