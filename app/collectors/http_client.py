import time

import httpx

from app.core.config import settings


class HttpClient:

    def __init__(self):

        self.client = httpx.Client(
            timeout=settings.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64)"
                )
            },
        )

    def get(self, url: str):

        for attempt in range(settings.retries):

            try:

                response = self.client.get(url)

                response.raise_for_status()

                return response

            except httpx.HTTPError:

                if attempt == settings.retries - 1:
                    raise

                time.sleep(2**attempt)