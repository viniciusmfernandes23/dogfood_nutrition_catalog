from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"

INTERMEDIATE_DIR = DATA_DIR / "intermediate"

OUTPUT_DIR = DATA_DIR / "output"

DATASET_DIR = DATA_DIR / "dataset"

REPORT_DIR = DATA_DIR / "reports"

for directory in (
    RAW_DIR,
    INTERMEDIATE_DIR,
    OUTPUT_DIR,
    DATASET_DIR,
    REPORT_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)

API_URL = "https://www.cobasi.com.br/api/catalog_system/pub/products/search"  # noqa: E501
# Nota: a API VTEX da Cobasi exige path de navegação + map=c,c[,c]
# para filtrar subcategorias. O parâmetro fq=C:ID só funciona no departamento raiz.

PAGE_SIZE = 50

HTTP_TIMEOUT = 30

MAX_RETRIES = 3

REQUEST_DELAY = 0.3