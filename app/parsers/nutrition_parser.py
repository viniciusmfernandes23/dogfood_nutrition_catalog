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

def clean_numeric_value(raw_val: str) -> float | None:
    """
    Limpa strings numéricas tratando separadores de milhar e decimais.
    Ex: '3.700' -> 3700.0, '1.055,15' -> 1055.15
    """
    try:
        # Se tem vírgula e ponto, a vírgula é decimal (padrão BR)
        if "." in raw_val and "," in raw_val:
            return float(raw_val.replace(".", "").replace(",", "."))
        
        # Se tem apenas vírgula, é decimal
        if "," in raw_val:
            return float(raw_val.replace(",", "."))
        
        # Se tem apenas ponto, pode ser milhar (3.700) ou decimal (3.7)
        if "." in raw_val:
            parts = raw_val.split(".")
            # Heurística: se a última parte tem 3 dígitos, é milhar (ex: 3.700, 10.530)
            # A menos que seja um valor muito pequeno (ex: 1.234 pode ser milhar ou decimal, 
            # mas em ração 1.234 kcal é improvável ser decimal se não tiver vírgula).
            if len(parts[-1]) == 3:
                return float(raw_val.replace(".", ""))
            return float(raw_val)
            
        return float(raw_val)
    except (ValueError, IndexError):
        return None

def parse_nutrition(
    raw_text: Any,
) -> dict[str, dict[str, Any]]:
    """
    Extrai todos os nutrientes encontrados na seção 'Níveis de Garantia'.
    """

    if not isinstance(raw_text, str) or not raw_text.strip():
        return {}

    text = raw_text.lower()
    parsed: dict[str, dict[str, Any]] = {}
    all_matches = []

    for nutrient, aliases in NUTRIENT_ALIASES.items():
        for alias in aliases:
            boundary = r"\b" if (len(alias) <= 2 and re.match(r"^\w+$", alias)) else ""
            
            if "\\" in alias or "(" in alias or ")" in alias:
                pattern_str = alias
            elif "." in alias:
                pattern_str = re.escape(alias).replace(r"\.", r"\.?")
            else:
                pattern_str = re.escape(alias)
                
            # Regex de número que aceita separadores de milhar e decimais
            NUMBER_EXT = r"(\d+(?:[.,]\d+)*)"
            pattern = re.compile(
                rf"{boundary}{pattern_str}{boundary}"
                rf"[:\s]*" 
                rf"{SEPARATOR}"
                rf"{NUMBER_EXT}"
                rf"\s*"
                rf"{UNIT}",
                FLAGS,
            )
            
            for match in pattern.finditer(text):
                raw_val = match.group(1)
                value = clean_numeric_value(raw_val)
                
                if value is None:
                    continue
                    
                unit = match.group(2).strip().lower() if match.group(2) else None
                
                # Normalização de unidades no parser
                if unit in ["%", "por cento", "porcentagem"]:
                    unit = "%"
                elif unit in ["g/kg", "g / kg", "g.kg", "g"]:
                    unit = "g/kg"
                elif unit in ["mg/kg", "mg / kg", "mg.kg", "mg"]:
                    unit = "mg/kg"
                elif unit in ["ui/kg", "ui / kg", "ui.kg", "ui", "u.i.", "u.i"]:
                    unit = "ui/kg"
                elif unit in ["mcg", "ug"]:
                    unit = "mcg"
                elif unit and ("kcal" in unit and "100" in unit):
                    unit = "kcal/100g"
                elif unit in ["kcal/kg", "kcal / kg", "kcal.kg", "kcal", "cal/kg", "cal"]:
                    unit = "kcal/kg"
                elif unit in ["kcal/sachê", "kcal/sache"]:
                    unit = "kcal/sache"
                elif unit and ("mj" in unit and "kg" in unit):
                    unit = "mj/kg"

                all_matches.append({
                    "nutrient": nutrient,
                    "value": value,
                    "unit": unit,
                    "matched_alias": alias,
                    "start": match.start(),
                    "end": match.end(),
                    "full_text": match.group(0)
                })

    all_matches.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    used_positions = set()
    
    for m in all_matches:
        is_overlapping = False
        for p in range(m["start"], m["end"]):
            if p in used_positions:
                is_overlapping = True
                break
        
        if is_overlapping:
            continue
            
        nut_key = f"{m['nutrient']}_{m['start']}"
        parsed[nut_key] = {
            "nutrient": m["nutrient"],
            "value": m["value"],
            "unit": m["unit"],
            "matched_alias": m["matched_alias"],
            "start": m["start"],
            "end": m["end"]
        }
        
        for p in range(m["start"], m["end"]):
            used_positions.add(p)

    return parsed
