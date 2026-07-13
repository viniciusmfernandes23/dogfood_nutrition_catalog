from __future__ import annotations

import re

# Suporta 1.000,00 ou 1000,00 ou 1000.00
NUMBER = r"(\d+(?:[.,]\d+)?)"
UNIT = r"(mg/kg|g/kg|ppm|ui/kg|ui|%|kcal/kg|kcal/g|kcal|cal/kg|cal/g)"
SEPARATOR = r"[^0-9%]{0,10}?"

FLAGS = re.IGNORECASE | re.MULTILINE