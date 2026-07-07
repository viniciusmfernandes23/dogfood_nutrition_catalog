from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from enum import Enum
from functools import lru_cache


class SemanticClassifier:
    """
    Classificador semântico baseado em palavras-chave.
    """

    def __init__(
        self,
        rules: Mapping[Enum, tuple[str, ...]],
    ) -> None:

        self.rules = rules

    # ==========================================================
    # Normalização
    # ==========================================================

    @staticmethod
    @lru_cache(maxsize=4096)
    def normalize_text(
        text: str | None,
    ) -> str:

        if not text:
            return ""

        text = unicodedata.normalize(
            "NFKD",
            text.lower(),
        )

        text = "".join(

            char

            for char

            in text

            if not unicodedata.combining(char)

        )

        text = re.sub(
            r"[^\w\s/-]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    @lru_cache(maxsize=8192)
    def _compile_pattern(
        keyword: str,
    ) -> re.Pattern[str]:

        keyword = SemanticClassifier.normalize_text(
            keyword,
        )

        return re.compile(
            rf"\b{re.escape(keyword)}\b",
            re.IGNORECASE,
        )

    @classmethod
    def contains_keyword(
        cls,
        text: str,
        keyword: str,
    ) -> bool:

        return bool(

            cls._compile_pattern(
                keyword,
            ).search(text)

        )

    # ==========================================================
    # Classificação
    # ==========================================================

    def classify(
        self,
        text: str | None,
    ) -> Enum | None:

        normalized = self.normalize_text(
            text,
        )

        for category, keywords in self.rules.items():

            if any(

                self.contains_keyword(
                    normalized,
                    keyword,
                )

                for keyword

                in keywords

            ):

                return category

        return None

    def classify_many(
        self,
        text: str | None,
    ) -> list[Enum]:

        normalized = self.normalize_text(
            text,
        )

        matches: list[Enum] = []

        for category, keywords in self.rules.items():

            if any(

                self.contains_keyword(
                    normalized,
                    keyword,
                )

                for keyword

                in keywords

            ):

                matches.append(category)

        return matches

    def has_match(
        self,
        text: str | None,
    ) -> bool:

        return self.classify(
            text,
        ) is not None

    # ==========================================================
    # Score
    # ==========================================================

    def score(
        self,
        text: str | None,
    ) -> dict[Enum, int]:

        normalized = self.normalize_text(
            text,
        )

        return {

            category: sum(

                self.contains_keyword(
                    normalized,
                    keyword,
                )

                for keyword

                in keywords

            )

            for category, keywords

            in self.rules.items()

        }

    def best_match(
        self,
        text: str | None,
    ) -> Enum | None:

        scores = self.score(
            text,
        )

        if not scores:

            return None

        best = max(
            scores,
            key=scores.get,
        )

        return (

            best

            if scores[best] > 0

            else None

        )

    # ==========================================================
    # Keywords
    # ==========================================================

    def extract_keywords(
        self,
        text: str | None,
    ) -> list[str]:

        normalized = self.normalize_text(
            text,
        )

        keywords = {

            keyword

            for values

            in self.rules.values()

            for keyword

            in values

            if self.contains_keyword(
                normalized,
                keyword,
            )

        }

        return sorted(
            keywords,
        )

    # ==========================================================
    # Explain
    # ==========================================================

    def explain(
        self,
        text: str | None,
    ) -> dict[str, object]:

        return {

            "best_match": self.best_match(
                text,
            ),

            "matches": self.classify_many(
                text,
            ),

            "keywords": self.extract_keywords(
                text,
            ),

            "scores": self.score(
                text,
            ),

        }