from __future__ import annotations

import re
from typing import Any

from app.parsers.aliases import NUTRIENT_ALIASES
from app.parsers.regex_patterns import (
    FLAGS,
    NUMBER,
    SEPARATOR,
    UNIT,
)


def parse_value(
    text: str,
    aliases: list[str],
) -> tuple[float | None, str | None, str | None]:
    """
    Procura o primeiro valor correspondente aos aliases informados.

    Returns:
        (
            value,
            unit,
            matched_alias,
        )
    """

    for alias in aliases:
        pattern = re.compile(
            rf"{re.escape(alias)}"
            rf"{SEPARATOR}"
            rf"{NUMBER}"
            rf"\s*"
            rf"{UNIT}",
            FLAGS,
        )

        match = pattern.search(text)

        if not match:
            continue

        try:
            raw_val = match.group(1)
            # Se tem ponto e vírgula, o ponto é milhar (ex: 1.500,00)
            if "." in raw_val and "," in raw_val:
                clean_val = raw_val.replace(".", "").replace(",", ".")
            # Se tem apenas vírgula e ela parece ser decimal (ex: 3500,00 ou 26,0)
            elif "," in raw_val:
                # Se tem apenas uma vírgula e 1 ou 2 dígitos depois, é decimal
                # Caso contrário, pode ser milhar (ex: 1,500) - mas no Brasil vírgula é decimal
                clean_val = raw_val.replace(",", ".")
            else:
                clean_val = raw_val
                
            value = float(clean_val)
            unit = match.group(2).strip().lower() if match.group(2) else None
            
            # Normalização básica de unidades comuns para facilitar o resolver
            if unit in ["%", "por cento", "porcentagem"]:
                unit = "%"
            elif unit in ["g/kg", "g / kg", "g.kg"]:
                unit = "g/kg"
            elif unit in ["mg/kg", "mg / kg", "mg.kg"]:
                unit = "mg/kg"
            elif unit in ["kcal/kg", "kcal / kg", "kcal.kg", "kcal", "cal/kg", "cal"]:
                unit = "kcal/kg"

            return (
                value,
                unit,
                alias,
            )
        except (ValueError, IndexError):
            continue

    return (
        None,
        None,
        None,
    )


def parse_nutrition(
    raw_text: Any,
) -> dict[str, dict[str, Any]]:
    """
    Extrai todos os nutrientes encontrados na seção
    'Níveis de Garantia'.

    Returns
    -------
    {
        "protein": {
            "value": 26.0,
            "unit": "%",
            "matched_alias": "proteína bruta",
        },
        ...
    }
    """

    # O pandas pode passar NaN (float) para esta função.
    # Verificamos se é uma string válida antes de processar.
    if not isinstance(raw_text, str) or not raw_text.strip():
        return {}

    text = raw_text.lower()

    parsed: dict[str, dict[str, Any]] = {}

    for nutrient, aliases in NUTRIENT_ALIASES.items():
        value, unit, matched_alias = parse_value(
            text=text,
            aliases=aliases,
        )

        if value is not None:
            parsed[nutrient] = {
                "value": value,
                "unit": unit,
                "matched_alias": matched_alias,
            }

    return parsed
