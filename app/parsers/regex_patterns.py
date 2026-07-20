from __future__ import annotations

import re

# Suporta 1.000,00 ou 1000,00 ou 1000.00
NUMBER = r"(\d+(?:[.,]\d+)?)"
UNIT = r"(mg/kg|g/kg|ppm|ui/kg|ui|%|kcal/100\s?g|kcal/kg|kcal/g|kcal|cal/kg|cal/g|kcal/sachê|kcal/sache|mj/kg|mj\s?/\s?kg)"
SEPARATOR = r"[^0-9%]{0,15}?"

FLAGS = re.IGNORECASE | re.MULTILINE