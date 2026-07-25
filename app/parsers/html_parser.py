from __future__ import annotations

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
    
    for i, line in enumerate(lines):
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
