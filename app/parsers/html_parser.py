from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Padrão para reconstituir separadores decimais fragmentados por quebras de
# linha.  O BeautifulSoup usa "\n" como separador entre elementos HTML, o que
# pode dividir um número decimal em duas linhas:
#   <td>7</td><td>,5</td>  →  "7\n,5"
#   <td>4</td><td>.052</td> →  "4\n.052"
#
# A regex abaixo detecta:
#   \d+          — parte inteira do número
#   \s*[\n\r]+\s* — quebra(s) de linha com espaços opcionais
#   [,.]         — separador decimal (vírgula ou ponto)
#   \d+          — parte decimal
#
# e reúne tudo em uma única linha sem espaços extras.
# ---------------------------------------------------------------------------
_DECIMAL_SPLIT_RE = re.compile(
    r"(\d+)\s*[\n\r]+\s*([,.])\s*(\d+)",
    re.MULTILINE,
)


def _normalize_split_decimals(text: str) -> str:
    """
    Reconstitui números decimais que foram fragmentados em linhas separadas
    pelo BeautifulSoup.

    Exemplos:
        "7\\n,5%"    → "7,5%"
        "4\\n.052 kcal/kg" → "4.052 kcal/kg"
        "26\\n,0%"   → "26,0%"

    A substituição é aplicada iterativamente até não haver mais fragmentações,
    para cobrir casos aninhados (ex: "1\\n.\\n234").
    """
    prev = None
    result = text
    while result != prev:
        prev = result
        result = _DECIMAL_SPLIT_RE.sub(r"\1\2\3", result)
    return result


def extract_guarantee_section(
    html: str | None,
) -> str | None:

    if html is None:
        return None

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    text = soup.get_text(
        "\n",
        strip=True,
    )

    # v1.5.8: Reconstituir números decimais fragmentados por quebras de linha.
    # O BeautifulSoup pode separar "7,5" em "7\n,5" quando a vírgula decimal
    # está em um elemento HTML distinto do dígito inteiro.  Isso causava o
    # parser a capturar apenas a parte inteira (ex: "7") e, após a conversão
    # de percentual pelo resolver (×10), produzir valores com fator de erro ×10.
    text = _normalize_split_decimals(text)

    lines = text.splitlines()

    start = None

    # v1.5.5: Aliases exaustivos para seção de garantia
    guarantee_markers = [
        "níveis de garantia",
        "niveis de garantia",
        "garantia",
        "análise garantida",
        "analise garantida",
        "composição",
        "composicao",
        "constituintes analíticos",
        "componentes analíticos",
        "análise média",
        "informação nutricional",
        "informacao nutricional",
        "levels of guarantee",
        "guaranteed analysis",
    ]

    # Prioriza a tabela nutricional quando a página também possui uma seção de
    # composição com minerais ou outros termos que parecem nutrientes.
    preferred_markers = (
        "níveis de garantia",
        "niveis de garantia",
        "análise garantida",
        "analise garantida",
        "guaranteed analysis",
    )
    for i, line in enumerate(lines):
        if line.lower().strip() in preferred_markers:
            start = i
            break
    
    for i, line in enumerate(lines):
        if start is not None:
            break
        line_lower = line.lower()
        # v1.5.5: Busca por match exato ou início de linha para evitar falsos positivos
        if any(marker in line_lower for marker in guarantee_markers):
            # Verificação adicional: a seção de garantia costuma ter valores numéricos próximos
            # Olhamos as próximas 10 linhas em busca de padrões de nutrientes (%, g/kg, mg/kg)
            found_values = False
            for j in range(i, min(i + 15, len(lines))):
                if any(u in lines[j].lower() for u in ["%", "g/kg", "mg/kg", "kcal", "ui/kg"]):
                    found_values = True
                    break
            
            if found_values:
                start = i
                break

    if start is None:

        return None

    end = len(lines)

    for i in range(start + 1, len(lines)):

        lower = lines[i].lower()

        if "ficha técnica" in lower:

            end = i

            break

    return "\n".join(lines[start:end])


def extract_ingredients_section(
    html: str | None,
) -> str | None:
    """Extrai a lista de ingredientes da página do produto."""
    if html is None:
        return None

    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines()]
    markers = (
        "ingredientes",
        "ingredients",
        "composição",
        "composicao",
        "composição básica",
        "composicao basica",
        "composição da receita",
        "composicao da receita",
    )
    end_markers = (
        "níveis de garantia",
        "niveis de garantia",
        "análise garantida",
        "analise garantida",
        "componentes analíticos",
        "componentes analiticos",
        "ficha técnica",
        "ficha tecnica",
        "modo de usar",
        "indicações",
        "indicacoes",
        "informação nutricional",
        "informacao nutricional",
        "tabela nutricional",
        "modo de conservação",
        "modo de conservacao",
        "quantidade",
        "composição analítica",
        "composicao analitica",
    )
    end_markers = set(end_markers)
    end_markers.update(
        tag.get_text(" ", strip=True).lower().rstrip(":").strip()
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    )
    heading_markers = {
        tag.get_text(" ", strip=True).lower().rstrip(":").strip()
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if "ingrediente" in tag.get_text(" ", strip=True).lower()
    }

    for index, line in enumerate(lines):
        normalized = line.lower().rstrip(":").strip()
        marker = next(
            (item for item in markers if normalized.startswith(f"{item}:")),
            None,
        )
        is_ingredients_heading = normalized in heading_markers
        if normalized not in markers and marker is None and not is_ingredients_heading:
            continue

        ingredients = []
        inline_value = line[len(marker) + 1:].strip() if marker else ""
        if inline_value:
            ingredients.append(inline_value)
        for candidate in lines[index + 1:]:
            if candidate.lower().rstrip(":").strip() in end_markers:
                break
            if candidate:
                ingredients.append(candidate)

        value = " ".join(ingredients).strip()
        return value or None

    return None


def extract_product_ratings(html: str | None) -> dict[str, float | int | None]:
    """Extrai nota, total e distribuição de estrelas sem coletar comentários."""
    empty = {
        "rating_average": None,
        "rating_count": None,
        "rating_1_star": None,
        "rating_2_star": None,
        "rating_3_star": None,
        "rating_4_star": None,
        "rating_5_star": None,
    }
    if not html:
        return empty

    soup = BeautifulSoup(html, "html.parser")
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        try:
            payload = json.loads(next_data.string or next_data.get_text())
            product_detail = payload.get("props", {}).get("pageProps", {}).get(
                "productDetail", {}
            )
            product_rating = product_detail.get("productRating") or {}
            stars = product_rating.get("stars") or {}
            if product_rating.get("avg") is not None:
                empty["rating_average"] = float(
                    str(product_rating["avg"]).replace(",", ".")
                )
            if stars:
                for star in range(1, 6):
                    value = stars.get(str(star))
                    empty[f"rating_{star}_star"] = (
                        int(value) if value is not None else None
                    )
                empty["rating_count"] = sum(
                    value for value in stars.values()
                    if isinstance(value, (int, float))
                )
            if any(value is not None for value in empty.values()):
                return empty
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.string or script.get_text())
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        ratings = payload.get("aggregateRating") if isinstance(payload, dict) else None
        if not isinstance(ratings, dict):
            continue
        if ratings.get("ratingValue") is not None:
            empty["rating_average"] = float(ratings["ratingValue"])
        if ratings.get("reviewCount") is not None:
            empty["rating_count"] = int(ratings["reviewCount"])
        return empty

    return empty


def extract_product_comments(html: str | None) -> list[str]:
    """Extrai textos de comentários de avaliações presentes na página."""
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    comments: list[str] = []

    def add_comment(value: object) -> None:
        if not isinstance(value, str):
            return
        comment = " ".join(value.split())
        if comment and comment not in comments:
            comments.append(comment)

    def collect_review_values(value: object) -> None:
        if isinstance(value, str):
            add_comment(value)
            return
        if isinstance(value, list):
            for item in value:
                collect_review_values(item)
            return
        if not isinstance(value, dict):
            return

        for key in (
            "comment",
            "text",
            "body",
            "content",
            "reviewText",
            "reviewBody",
        ):
            add_comment(value.get(key))

    def find_review_collections(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = str(key).lower()
                if normalized_key in {
                    "reviews",
                    "review",
                    "customerreviews",
                    "reviewlist",
                    "userreviews",
                    "comments",
                }:
                    collect_review_values(nested)
                find_review_collections(nested)
        elif isinstance(value, list):
            for nested in value:
                find_review_collections(nested)

    for script in soup.find_all("script"):
        script_text = script.string or script.get_text()
        if not script_text or "review" not in script_text.lower():
            continue
        try:
            find_review_collections(json.loads(script_text))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

    for element in soup.select(
        '[data-review-text], [data-testid*="review"], .review-text, .review-comment'
    ):
        add_comment(element.get("data-review-text"))
        add_comment(element.get_text(" ", strip=True))

    return comments
