from __future__ import annotations

from bs4 import BeautifulSoup

from app.collectors.http_client import HttpClient


class CobasiCrawler:

    def __init__(self):

        self.client = HttpClient()

    def fetch_html(
        self,
        url: str,
    ) -> str | None:

        try:

            response = self.client.get(url)

            html = response.text

            if "captcha" in html.lower():
                return None

            return html

        except Exception:

            return None

    @staticmethod
    def extract_raw_text(
        html: str | None,
    ) -> str | None:

        if html is None:
            return None

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        text = soup.get_text(
            separator="\n",
            strip=True,
        )

        lines = text.splitlines()

        start = None

        for i, line in enumerate(lines):

            if "níveis de garantia" in line.lower():

                start = i

                break

        if start is None:
            return None

        end = len(lines)

        for i in range(start + 1, len(lines)):

            if "ficha técnica" in lines[i].lower():

                end = i

                break

        return "\n".join(lines[start:end])