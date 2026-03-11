"""Configuration globale de l'application."""

from pathlib import Path

VERSION = "1.0.0"
APP_NAME = "Al Qalam Stock Manager"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMPORT_DIR = DATA_DIR / "imports"
EXPORT_DIR = DATA_DIR / "exports"
LOG_PATH = DATA_DIR / "alqalam.log"
DB_PATH = DATA_DIR / "stock.db"

DB_ENGINE = "sqlite"
THEME_DEFAULT = "light"
ALERTE_INTERVALLE = 5

RACCOURCIS = {
    "nouveau": "Control-n",
    "export": "Control-e",
    "rafraichir": "F5",
}

COLONNES_STOCK = ["ref", "nom", "categorie", "qte", "prix_vente", "statut"]

for dossier in (DATA_DIR, IMPORT_DIR, EXPORT_DIR):
    dossier.mkdir(parents=True, exist_ok=True)

REQUIRED_CSV_COLUMNS = ['ref','nom','categorie','prix_achat','prix_vente','qte','seuil_min']

