# [V8 - CSV] Constantes globales du projet Al Qalam.

from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
IMPORTS_DIR = DATA_DIR / "imports"
CSV_DIR     = DATA_DIR / "csv"          # [V8] dossier dédié CSV

# ── Application ────────────────────────────────────────────────────────────
APP_NAME    = "Al Qalam — Gestion de Stock"
APP_VERSION = "8.0.0"
APP_WIDTH   = 1200
APP_HEIGHT  = 750

# ── Stock ──────────────────────────────────────────────────────────────────
SEUIL_MIN_DEFAUT = 5

# ── Surveillance (V4) ─────────────────────────────────────────────────────
INTERVALLE_SURVEILLANCE = 20   # secondes

# ── Couleurs (thème entreprise) ────────────────────────────────────────────
COULEUR_PRIMAIRE   = "#1F4E79"
COULEUR_SECONDAIRE = "#2E86C1"
COULEUR_ALERTE     = "#E74C3C"
COULEUR_OK         = "#27AE60"
COULEUR_FOND       = "#F0F4F8"
COULEUR_TEXTE      = "#2C3E50"
COULEUR_ORANGE     = "#E67E22"

# ── CSV V8 ────────────────────────────────────────────────────────────────
COLONNES_CATALOGUE_IMPORT = ["ref", "nom", "categorie", "prix_achat", "prix_vente", "seuil_min"]
COLONNES_CATALOGUE_EXPORT = ["ref", "nom", "categorie", "prix_achat", "prix_vente", "qte", "seuil_min"]
COLONNES_MOUVEMENTS       = ["date", "type", "ref", "produit", "qte", "note"]
COLONNES_COMPTABILITE     = ["ref", "nom", "categorie", "qte", "prix_achat", "prix_vente", "valeur_stock", "marge_unitaire", "marge_totale"]
