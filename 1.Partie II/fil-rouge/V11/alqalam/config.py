"""Configuration centrale du projet Al Qalam Stock Manager."""

from pathlib import Path

VERSION = "1.0.0"
APP_NAME = "Al Qalam Stock Manager"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMPORT_DIR = DATA_DIR / "imports"
EXPORT_DIR = DATA_DIR / "exports"
LOG_PATH = DATA_DIR / "alqalam.log"
JSON_PATH = DATA_DIR / "stock.json"
DB_PATH = DATA_DIR / "stock.db"
DB_ENGINE = "sqlite"

THEME_DEFAULT = "light"
ALERTE_INTERVALLE = 5

REQUIRED_CSV_COLUMNS = [
    "ref",
    "nom",
    "categorie",
    "prix_achat",
    "prix_vente",
    "qte",
    "seuil_min",
]

for path in (DATA_DIR, IMPORT_DIR, EXPORT_DIR):
    path.mkdir(parents=True, exist_ok=True)
