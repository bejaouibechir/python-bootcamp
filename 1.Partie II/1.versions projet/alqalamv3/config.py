# [V3 - Compréhensions] Constantes globales du projet Al Qalam.
# Modifier ici pour changer les paramètres sans toucher au code métier.

from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent          # racine du projet
DATA_DIR    = BASE_DIR / "data"              # données persistées
EXPORTS_DIR = DATA_DIR / "exports"          # fichiers exportés
IMPORTS_DIR = DATA_DIR / "imports"          # fichiers à importer

# ── Application ────────────────────────────────────────────────────────────
APP_NAME    = "Al Qalam — Gestion de Stock"
APP_VERSION = "3.0.0"
APP_WIDTH   = 1100
APP_HEIGHT  = 680

# ── Stock ──────────────────────────────────────────────────────────────────
SEUIL_MIN_DEFAUT = 5     # seuil d'alerte par défaut si non précisé

# ── Couleurs (thème entreprise) ────────────────────────────────────────────
COULEUR_PRIMAIRE  = "#1F4E79"   # bleu foncé  → boutons, en-têtes
COULEUR_SECONDAIRE= "#2E86C1"   # bleu moyen  → survol
COULEUR_ALERTE    = "#E74C3C"   # rouge       → produits en rupture
COULEUR_OK        = "#27AE60"   # vert        → statut OK
COULEUR_FOND      = "#F0F4F8"   # gris très clair → fond général
COULEUR_TEXTE     = "#2C3E50"   # gris foncé → texte principal
COULEUR_ORANGE    = "#E67E22"   # orange      → avertissements légers
