from __future__ import annotations

import re

NUMBER = r"(\d+(?:[.,]\d+)?)"

UNIT = r"(mg/kg|g/kg|ppm|ui/kg|ui|%|kcal/kg|kcal/g|kcal)"

SEPARATOR = r"[^0-9]{0,40}"

FLAGS = re.IGNORECASE | re.MULTILINE