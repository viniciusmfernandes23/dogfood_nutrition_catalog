from __future__ import annotations

import re
from collections.abc import Iterable
from enum import Enum


class SemanticClassifier:
    """
    Classificador semântico baseado em palavras-chave.

    Funciona para qualquer domínio:

    - Categoria do Produto
    - Fase de Vida
    - Porte
    - Categoria Clínica
    - Fonte de Proteína
    - Nível do Produto
    """

    def __init__(
        self,
        rules: dict[Enum, tuple[str, ...]],
    ) -> None:

        self.rules = rules

    @staticmethod
    def normalize_text(
        text: str | None,
    ) -> str:

        if text is None:
            return ""

        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def contains_keyword(
        text: str,
        keyword: str,
    ) -> bool:

        pattern = (
            rf"\b{re.escape(keyword.lower())}\b"
        )

        return bool(
            re.search(
                pattern,
                text,
            )
        )

    def classify(
        self,
        text: str | None,
    ) -> Enum | None:
        """
        Retorna a primeira categoria encontrada.
        """

        normalized = self.normalize_text(
            text,
        )

        for category, keywords in self.rules.items():

            for keyword in keywords:

                if self.contains_keyword(
                    normalized,
                    keyword,
                ):

                    return category

        return None

    def classify_many(
        self,
        text: str | None,
    ) -> list[Enum]:
        """
        Retorna todas as categorias encontradas.
        """

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

        return self.classify(text) is not None

    def score(
        self,
        text: str | None,
    ) -> dict[Enum, int]:
        """
        Calcula um score baseado
        no número de palavras-chave encontradas.
        """

        normalized = self.normalize_text(
            text,
        )

        scores: dict[Enum, int] = {}

        for category, keywords in self.rules.items():

            score = sum(

                self.contains_keyword(
                    normalized,
                    keyword,
                )

                for keyword

                in keywords

            )

            scores[category] = score

        return scores

    def best_match(
        self,
        text: str | None,
    ) -> Enum | None:
        """
        Retorna a categoria
        com maior score.
        """

        scores = self.score(text)

        if not scores:

            return None

        category = max(
            scores,
            key=scores.get,
        )

        if scores[category] == 0:

            return None

        return category

    def extract_keywords(
        self,
        text: str | None,
    ) -> list[str]:
        """
        Retorna todas as palavras-chave
        encontradas no texto.
        """

        normalized = self.normalize_text(
            text,
        )

        found: list[str] = []

        for keywords in self.rules.values():

            for keyword in keywords:

                if self.contains_keyword(
                    normalized,
                    keyword,
                ):

                    found.append(keyword)

        return sorted(
            set(found),
        )

    def explain(
        self,
        text: str | None,
    ) -> dict[str, object]:
        """
        Explica o processo
        de classificação.
        """

        return {

            "match": self.best_match(text),

            "matches": self.classify_many(text),

            "keywords": self.extract_keywords(text),

            "scores": self.score(text),

        }