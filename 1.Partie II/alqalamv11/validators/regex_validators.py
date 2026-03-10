# [V7 - Regex] Validateurs basés sur des expressions régulières.
#
# CONCEPT CLÉ :
#   On compile chaque pattern une seule fois avec re.compile() → performance optimale.
#   Chaque validateur retourne (valide: bool, message: str) pour l'affichage UI.
#
# PATTERNS UTILISÉS :
#   REF      : ^[A-Z]{2,6}-[A-Z0-9]{1,5}$     → CRAY-001, PAP-A4, STYL-002
#   NOM      : ^.{2,60}$                         → 2 à 60 caractères non vides
#   PRIX     : ^\d+([.,]\d{1,3})?$               → 0, 1.500, 12,90
#   QTE      : ^\d+$                             → entier non négatif
#   NOTE     : ^.{0,200}$                        → optionnel, max 200 caractères

import re

# ── Patterns compilés ─────────────────────────────────────────────────────────
# re.compile() : analyse la regex une fois → réutilisation sans reparser à chaque appel

REGEX = {
    # Référence produit : 2-6 lettres majuscules, tiret, 1-5 alphanum majuscules
    # Exemples valides : CRAY-001  PAP-A4  STYL-002  REG-001
    "ref": re.compile(r"^[A-Z]{2,6}-[A-Z0-9]{1,5}$"),

    # Nom produit : entre 2 et 60 caractères (tout sauf vide)
    "nom": re.compile(r"^.{2,60}$"),

    # Prix : entier ou décimal avec virgule/point, 1 à 3 décimales
    # Exemples valides : 0  1.5  12,90  0.300
    "prix": re.compile(r"^\d+([.,]\d{1,3})?$"),

    # Quantité / seuil : entier positif ou nul
    "qte": re.compile(r"^\d+$"),

    # Note : optionnelle, max 200 caractères
    "note": re.compile(r"^.{0,200}$", re.DOTALL),

    # Pattern de log interne — utilisé par LogParser pour analyser les entrées journal
    # Format : [2025-03-09 10:42:01] [entree  ] ✅ CRAY-001 | Entrée stock | +50 unités
    "log_ligne": re.compile(
        r"\[(?P<date>\d{4}-\d{2}-\d{2}) (?P<heure>\d{2}:\d{2}:\d{2})\]"
        r"\s\[(?P<operation>[\w]+)\s*\]"
        r"\s(?P<icone>[✅❌🔹📥📤➕🗑️✏️⚖️↩️]+)"
        r"\s(?P<ref>[\w-]+)"
        r"\s\|\s(?P<label>[^|]+)"
        r"\s\|\s(?P<details>.+)",
        re.UNICODE,
    ),

    # Extraction de la quantité dans les détails (ex: "+50", "-3", "cible=45")
    "details_qte": re.compile(r"[+-]?\d+"),

    # Extraction d'une référence produit dans un texte libre
    "ref_dans_texte": re.compile(r"\b[A-Z]{2,6}-[A-Z0-9]{1,5}\b"),
}


# ── Fonctions de validation ────────────────────────────────────────────────────

def valider_ref(texte: str) -> tuple[bool, str]:
    """
    Valide la référence produit.

    Format attendu : 2-6 lettres MAJ + tiret + 1-5 alphanum MAJ
    Exemples valides : CRAY-001  PAP-A4  STYL-002
    Exemples invalides : cray-001 (minuscules)  REF-12345678 (trop long)
    """
    t = texte.strip().upper()
    if not t:
        return False, "La référence est obligatoire."
    if REGEX["ref"].match(t):
        return True, "✓ Référence valide"
    return False, "Format attendu : 2-6 lettres MAJ + tiret + 1-5 alphanum (ex: CRAY-001)"


def valider_nom(texte: str) -> tuple[bool, str]:
    """
    Valide le nom du produit (2 à 60 caractères).
    """
    t = texte.strip()
    if not t:
        return False, "Le nom est obligatoire."
    if REGEX["nom"].match(t):
        return True, "✓ Nom valide"
    return False, "Le nom doit comporter entre 2 et 60 caractères."


def valider_prix(texte: str) -> tuple[bool, str]:
    """
    Valide un prix en TND.

    Accepte : entier (0, 5) ou décimal avec , ou . (1.500, 12,90).
    Remplace la virgule par un point avant conversion dans _valider().
    """
    t = texte.strip()
    if not t:
        return False, "Le prix est obligatoire."
    if REGEX["prix"].match(t):
        return True, "✓ Prix valide"
    return False, "Format attendu : nombre entier ou décimal (ex: 1.500 ou 12,90)"


def valider_qte(texte: str, obligatoire: bool = True) -> tuple[bool, str]:
    """
    Valide une quantité ou un seuil (entier ≥ 0).

    Si obligatoire=False, une chaîne vide est acceptée (défaut = 0).
    """
    t = texte.strip()
    if not t:
        if obligatoire:
            return False, "La quantité est obligatoire."
        return True, "✓ (valeur par défaut : 0)"
    if REGEX["qte"].match(t):
        return True, "✓ Quantité valide"
    return False, "La quantité doit être un entier ≥ 0."


def valider_note(texte: str) -> tuple[bool, str]:
    """
    Valide une note optionnelle (max 200 caractères).
    Toujours valide — la note est facultative.
    """
    t = texte.strip()
    if len(t) > 200:
        return False, f"Note trop longue ({len(t)}/200 caractères)."
    return True, f"✓ Note acceptée ({len(t)}/200)"
