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

    Regras (padrão brasileiro):
      - Ponto + vírgula presentes  → ponto é milhar, vírgula é decimal
        Ex: '1.055,15' → 1055.15
      - Apenas vírgula             → vírgula é decimal
        Ex: '7,5' → 7.5,  '26,0' → 26.0
      - Apenas ponto               → heurística de milhar:
          * Exatamente 3 dígitos após o ponto → milhar
            Ex: '3.700' → 3700.0,  '4.052' → 4052.0
          * Qualquer outro número de dígitos → decimal
            Ex: '7.5' → 7.5,  '7.50' → 7.5,  '40.52' → 40.52
      - Sem separador              → inteiro
        Ex: '75' → 75.0

    Nota sobre o fator de erro ×10:
      O bug sistemático ocorre quando o HTML separa o número decimal em
      elementos distintos (ex: <td>7</td><td>,5</td>), fazendo o
      BeautifulSoup gerar "7\\n,5".  O html_parser.py normaliza esse padrão
      antes de chamar o parser.  Aqui garantimos que, se a vírgula chegar
      intacta no raw_val, ela seja corretamente convertida para ponto decimal
      (replace(",", ".")) e nunca removida silenciosamente.
    """
    if not isinstance(raw_val, str):
        return None

    # Remove espaços internos que possam ter sido introduzidos por formatação
    raw_val = raw_val.strip()
    if not raw_val:
        return None

    try:
        # Caso 1: tem vírgula E ponto → padrão BR (ponto = milhar, vírgula = decimal)
        if "." in raw_val and "," in raw_val:
            return float(raw_val.replace(".", "").replace(",", "."))

        # Caso 2: apenas vírgula → vírgula é decimal
        # IMPORTANTE: usar replace(",", ".") e NUNCA replace(",", "")
        # para evitar o fator de erro ×10 (ex: '7,5' → 75 em vez de 7.5).
        if "," in raw_val:
            return float(raw_val.replace(",", "."))

        # Caso 3: apenas ponto → heurística de milhar
        if "." in raw_val:
            parts = raw_val.split(".")
            # Heurística: exatamente 3 dígitos após o ponto → separador de milhar BR
            # (ex: '3.700' → 3700, '4.052' → 4052, '10.530' → 10530)
            # Qualquer outro caso → ponto decimal
            # (ex: '7.5' → 7.5, '7.50' → 7.5, '40.52' → 40.52)
            if len(parts) == 2 and len(parts[-1]) == 3 and parts[-1].isdigit():
                return float(raw_val.replace(".", ""))
            return float(raw_val)

        # Caso 4: sem separador → inteiro
        return float(raw_val)

    except (ValueError, IndexError):
        return None


def parse_value(
    text: str,
    aliases: list[str],
) -> tuple[float | None, str | None, str | None]:
    """
    Procura o primeiro valor correspondente aos aliases informados no texto.

    Retorna uma tupla (value, unit, alias) onde:
      - value: o valor numérico extraído (float) ou None se não encontrado
      - unit: a unidade normalizada (str) ou None
      - alias: o alias que produziu o match (str) ou None

    Internamente usa clean_numeric_value() para garantir que separadores
    decimais BR sejam tratados corretamente e evitar o fator de erro ×10.
    """
    for alias in aliases:
        boundary = r"\b" if (len(alias) <= 2 and re.match(r"^\w+$", alias)) else ""

        if "\\" in alias or "(" in alias or ")" in alias:
            pattern_str = alias
        elif "." in alias:
            pattern_str = re.escape(alias).replace(r"\.", r"\.?")
        else:
            pattern_str = re.escape(alias)

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

        match = pattern.search(text)
        if not match:
            continue

        raw_val = match.group(1)
        value = clean_numeric_value(raw_val)
        if value is None:
            continue

        unit = match.group(2).strip().lower() if match.group(2) else None

        # Normalização de unidades (espelho do parse_nutrition)
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

        return (value, unit, alias)

    return (None, None, None)


def parse_nutrition(
    raw_text: Any,
) -> dict[str, dict[str, Any]]:
    """
    Extrai todos os nutrientes encontrados na seção 'Níveis de Garantia'.

    O texto de entrada deve ter sido previamente normalizado pelo
    html_parser.extract_guarantee_section(), que reconstitui números decimais
    fragmentados por quebras de linha (bug de fator ×10).
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

            # Regex de número que aceita separadores de milhar e decimais.
            #
            # Padrão: \d+(?:[.,]\d+)*
            #   - \d+          → parte inteira obrigatória
            #   - (?:[.,]\d+)* → zero ou mais grupos de (separador + dígitos)
            #
            # Isso captura corretamente:
            #   '7,5'     → '7,5'   (decimal BR)
            #   '3.700'   → '3.700' (milhar BR)
            #   '4.052'   → '4.052' (milhar BR)
            #   '1.055,15'→ '1.055,15' (milhar + decimal BR)
            #
            # O SEPARATOR = r"[^0-9%]{0,50}?" (lazy, exclui dígitos e '%')
            # garante que a vírgula decimal nunca seja consumida pelo separador,
            # pois ela é sempre precedida por um dígito que o SEPARATOR não pode
            # consumir.
            NUMBER_EXT = r"(\d+(?:[.,]\d+)*)"
            value_separator = SEPARATOR
            if nutrient == "metabolizable_energy":
                value_separator = (
                    r"(?:\s*(?:\([^)]*\)|mín\.?|min\.?))?"
                    r"\s*[:\-]?\s*"
                )
            pattern = re.compile(
                rf"{boundary}{pattern_str}{boundary}"
                rf"[:\s]*"
                rf"{value_separator}"
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
                elif unit in ["kcal/und", "kcal/unidade"]:
                    # Energia por unidade não é comparável a kcal/kg sem o peso
                    # individual; permanece fora do catálogo normalizado.
                    continue
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

        if nutrient == "metabolizable_energy":
            for match in re.finditer(
                rf"energia\s+metabolizável\s+kcal\s*/\s*kg\s*{NUMBER_EXT}",
                text,
                FLAGS,
            ):
                all_matches.append({
                    "nutrient": nutrient,
                    "value": clean_numeric_value(match.group(1)),
                    "unit": "kcal/kg",
                    "matched_alias": "energia metabolizável kcal/kg",
                    "start": match.start(),
                    "end": match.end(),
                    "full_text": match.group(0),
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
