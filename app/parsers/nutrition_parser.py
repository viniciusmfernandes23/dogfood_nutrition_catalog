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
    """

    for alias in aliases:
        # v1.3.15: Proteção contra matches parciais (ex: 'p' dando match em 'potássio')
        # Usamos \b apenas se o alias for curto e alfanumérico para evitar falsos positivos.
        # Se for um alias longo ou com regex (ex: \(mín\)), confiamos na especificidade do alias.
        boundary = r"\b" if (len(alias) <= 2 and re.match(r"^\w+$", alias)) else ""
        pattern_str = alias if "\\" in alias else re.escape(alias)
        
        pattern = re.compile(
            rf"{boundary}{pattern_str}{boundary}"
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
            if "." in raw_val and "," in raw_val:
                clean_val = raw_val.replace(".", "").replace(",", ".")
            elif "," in raw_val:
                clean_val = raw_val.replace(",", ".")
            elif "." in raw_val:
                parts = raw_val.split(".")
                if len(parts) == 2 and len(parts[1]) == 3:
                    clean_val = raw_val.replace(".", "")
                else:
                    clean_val = raw_val
            else:
                clean_val = raw_val
                
            value = float(clean_val)
            unit = match.group(2).strip().lower() if match.group(2) else None
            
            if unit in ["%", "por cento", "porcentagem"]:
                unit = "%"
            elif unit in ["g/kg", "g / kg", "g.kg"]:
                unit = "g/kg"
            elif unit in ["mg/kg", "mg / kg", "mg.kg"]:
                unit = "mg/kg"
            elif unit in ["kcal/100g", "kcal / 100g", "kcal/100 g"]:
                unit = "kcal/100g"
            elif unit in ["kcal/kg", "kcal / kg", "kcal.kg", "kcal", "cal/kg", "cal"]:
                unit = "kcal/kg"
            elif unit in ["kcal/sachê", "kcal/sache"]:
                unit = "kcal/sache"
            elif unit in ["mj/kg", "mj / kg"]:
                unit = "mj/kg"

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
    """

    if not isinstance(raw_text, str) or not raw_text.strip():
        return {}

    text = raw_text.lower()
    parsed: dict[str, dict[str, Any]] = {}
    
    all_matches = []

    for nutrient, aliases in NUTRIENT_ALIASES.items():
        for alias in aliases:
            # v1.3.15: Proteção contra matches parciais (ex: 'p' dando match em 'potássio')
            boundary = r"\b" if (len(alias) <= 2 and re.match(r"^\w+$", alias)) else ""
            
            # v1.3.13: Se o alias já contém escape de regex (como \(mín\)), usamos como está.
            # Caso contrário, escapamos caracteres especiais.
            if "\\" in alias or "(" in alias or ")" in alias:
                pattern_str = alias
            else:
                pattern_str = re.escape(alias)
                
            pattern = re.compile(
                rf"{boundary}{pattern_str}{boundary}"
                rf"{SEPARATOR}"
                rf"{NUMBER}"
                rf"\s*"
                rf"{UNIT}",
                FLAGS,
            )
            
            for match in pattern.finditer(text):
                try:
                    raw_val = match.group(1)
                    if "." in raw_val and "," in raw_val:
                        clean_val = raw_val.replace(".", "").replace(",", ".")
                    elif "," in raw_val:
                        clean_val = raw_val.replace(",", ".")
                    elif "." in raw_val:
                        parts = raw_val.split(".")
                        if len(parts) == 2 and len(parts[1]) == 3:
                            clean_val = raw_val.replace(".", "")
                        else:
                            clean_val = raw_val
                    else:
                        clean_val = raw_val
                        
                    value = float(clean_val)
                    unit = match.group(2).strip().lower() if match.group(2) else None
                    
                    if unit in ["%", "por cento", "porcentagem"]:
                        unit = "%"
                    elif unit in ["g/kg", "g / kg", "g.kg"]:
                        unit = "g/kg"
                    elif unit in ["mg/kg", "mg / kg", "mg.kg"]:
                        unit = "mg/kg"
                    elif unit in ["kcal/100g", "kcal / 100g", "kcal/100 g"]:
                        unit = "kcal/100g"
                    elif unit in ["kcal/kg", "kcal / kg", "kcal.kg", "kcal", "cal/kg", "cal"]:
                        unit = "kcal/kg"
                    elif unit in ["kcal/sachê", "kcal/sache"]:
                        unit = "kcal/sache"
                    elif unit in ["mj/kg", "mj / kg"]:
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
                except (ValueError, IndexError):
                    continue

    # Resolve conflitos: prioriza a ordem de aparecimento no texto.
    # Se dois matches começam na mesma posição, prioriza o mais longo.
    all_matches.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    
    used_positions = set()
    
    for m in all_matches:
        # v1.3.14: Lógica de sobreposição e coexistência definitiva.
        # Ignoramos se a posição inicial já foi consumida.
        is_overlapping = False
        for p in range(m["start"], m["end"]):
            if p in used_positions:
                is_overlapping = True
                break
        
        if is_overlapping:
            continue
            
        # Criamos uma chave única baseada no nutriente e na posição para permitir a extração
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
