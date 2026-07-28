"""
Utilidades internas de parsing de peso de SKU.

Centralizadas aqui para evitar duplicação entre o executar_pipeline.py
e os coletores específicos (Cobasi, Petlove).
"""

from __future__ import annotations

import re


_WEIGHT_PATTERN = re.compile(
    r"(?:(\d+(?:[.,]\d+)?)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g)\b",
    re.IGNORECASE,
)


def cobasi_parse_weight(sku_name: str | None) -> float | None:
    """
    Extrai o peso em kg a partir do nome do SKU.

    Suporta formatos como "15kg", "10,1 kg", "500g", "2x15kg".
    Retorna None quando não é possível determinar o peso.
    """
    if not sku_name:
        return None

    match = _WEIGHT_PATTERN.search(sku_name)
    if not match:
        return None

    multiplier_str, value_str, unit = match.groups()

    # Normaliza separador decimal (vírgula → ponto)
    value = float(value_str.replace(",", "."))

    if unit.lower() == "g":
        value = value / 1000.0

    if multiplier_str:
        multiplier = float(multiplier_str.replace(",", "."))
        value = multiplier * value

    return round(value, 4)
