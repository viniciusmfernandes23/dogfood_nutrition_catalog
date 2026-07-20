from __future__ import annotations

import re

# Suporta 1.000,00 ou 1000,00 ou 1000.00
NUMBER = r"(\d+(?:[.,]\d+)?)"
UNIT = r"(mg/kg|mg\s?/\s?kg|g/kg|g\s?/\s?kg|ppm|ui/kg|ui\s?/\s?kg|ui|u\.i\.|mcg|mg|g|%|kcal/100\s?g|kcal/kg|kcal/g|kcal|cal/kg|cal/g|kcal/sachê|kcal/sache|mj/kg|mj\s?/\s?kg)"
SEPARATOR = r"[^0-9%]{0,50}?"

FLAGS = re.IGNORECASE | re.MULTILINE