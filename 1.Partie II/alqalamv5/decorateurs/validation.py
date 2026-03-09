# [V5 - Décorateurs] Décorateurs de validation et de mesure de performance.
#
# Deux formes de décorateurs illustrées ici :
#
#  1. Décorateur SIMPLE (sans paramètre) : @chronometre
#     → Une seule fonction enveloppe → prend func en argument directement
#
#  2. Décorateur AVEC PARAMÈTRE : @valider_qte(min_val=1)
#     → Fabrique → retourne un vrai décorateur
#
# Règle mnémotechnique :
#   @deco          → def deco(func): ...
#   @deco(x)       → def deco(x): def decorateur(func): ... return decorateur

import functools
import time


# ── 1. Décorateur simple : chronomètre ──────────────────────────────────────

def chronometre(func):
    """
    Décorateur simple (sans paramètre) qui mesure la durée d'exécution.

    Usage :
        @chronometre
        def ma_fonction():
            ...

    Utile pour identifier les goulots d'étranglement (sauvegarde JSON lente, etc.).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        debut    = time.perf_counter()   # horloge haute précision
        resultat = func(*args, **kwargs)
        fin      = time.perf_counter()
        duree_ms = (fin - debut) * 1000
        # Affichage discret — en production on écrirait dans un fichier de log
        print(f"[⏱ chrono] {func.__qualname__}  →  {duree_ms:.2f} ms")
        return resultat
    return wrapper


# ── 2. Décorateur avec paramètre : validation de quantité ───────────────────

def valider_qte(min_val: int = 1, max_val: int = 100_000):
    """
    Fabrique de décorateur — valide la quantité passée en 2e argument.

    Usage :
        @valider_qte(min_val=1, max_val=10_000)
        def entree_stock(self, ref, qte, note=""):
            ...

    La quantité est supposée être le 2e argument positionnel (indice 1).
    Lève ValueError avec un message clair avant même d'entrer dans la méthode.
    """
    def decorateur(func):
        @functools.wraps(func)
        def wrapper(self, ref, qte, *args, **kwargs):
            # Validation de type
            if not isinstance(qte, int):
                raise TypeError(
                    f"[{func.__name__}] La quantité doit être un entier, "
                    f"reçu : {type(qte).__name__}"
                )
            # Validation de plage
            if not (min_val <= qte <= max_val):
                raise ValueError(
                    f"[{func.__name__}] Quantité hors plage "
                    f"({min_val}–{max_val}), reçu : {qte}"
                )
            return func(self, ref, qte, *args, **kwargs)
        return wrapper
    return decorateur


# ── 3. Décorateur avec paramètre : validation de référence ──────────────────

def valider_ref(func):
    """
    Décorateur simple — vérifie que la référence (1er arg) est une chaîne non vide.

    Usage :
        @valider_ref
        def get_produit(self, ref):
            ...
    """
    @functools.wraps(func)
    def wrapper(self, ref, *args, **kwargs):
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError(
                f"[{func.__name__}] La référence doit être une chaîne non vide, "
                f"reçu : {ref!r}"
            )
        return func(self, ref.strip().upper(), *args, **kwargs)
    return wrapper
