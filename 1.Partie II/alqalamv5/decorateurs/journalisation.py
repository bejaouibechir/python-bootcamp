# [V5 - Décorateurs] Décorateur de journalisation automatique des opérations stock.
#
# Concepts démontrés :
#
#  @functools.wraps   → préserve __name__, __doc__, __module__ de la fonction décorée
#  Décorateur avec paramètre → fabrique de décorateurs (3 niveaux de fonctions imbriquées)
#  self._journal      → couplage léger : le décorateur accède au journal via l'instance
#
# Anatomie d'un décorateur avec paramètre :
#
#   journaliser("entree")          ← appel de la fabrique  → retourne 'decorateur'
#   def decorateur(func):          ← reçoit la fonction     → retourne 'wrapper'
#       def wrapper(self, ...):    ← remplace la fonction   → exécuté à chaque appel
#           ...
#       return wrapper
#   return decorateur

import functools
from datetime import datetime


def journaliser(operation: str):
    """
    Fabrique de décorateurs — enregistre automatiquement chaque opération
    dans le JournalService de l'instance StockService.

    Usage :
        @journaliser("entree")
        def entree_stock(self, ref, qte, note=""):
            ...

    La fonction décorée est enveloppée dans 'wrapper' qui :
      1. Mémorise l'heure de début
      2. Exécute la fonction originale
      3. Enregistre le succès (ou l'échec) dans self._journal
      4. Retourne le résultat (ou propage l'exception)
    """

    def decorateur(func):
        # [V5] @functools.wraps : copie les métadonnées de func → wrapper.
        # Sans @wraps, help(entree_stock) afficherait "wrapper" au lieu de "entree_stock".
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Premier argument positionnel = réf du produit (convention du projet)
            ref    = args[0] if args else "—"
            debut  = datetime.now()
            erreur = None

            try:
                resultat = func(self, *args, **kwargs)
                succes   = True
                return resultat

            except Exception as exc:
                succes = False
                erreur = str(exc)
                raise   # on propage toujours l'exception

            finally:
                # [V5] finally : s'exécute TOUJOURS, succès ou échec
                duree_ms = int((datetime.now() - debut).total_seconds() * 1000)
                # Accès à self._journal : le décorateur suppose que l'instance
                # possède un attribut _journal (contrat implicite avec StockService).
                if hasattr(self, "_journal"):
                    self._journal.enregistrer(
                        operation = operation,
                        ref       = ref,
                        details   = _formater_args(args, kwargs),
                        succes    = succes,
                        erreur    = erreur or "",
                        duree_ms  = duree_ms,
                    )

        return wrapper

    return decorateur   # la fabrique retourne le vrai décorateur


# ── Utilitaire interne ────────────────────────────────────────────────────────

def _formater_args(args: tuple, kwargs: dict) -> str:
    """Formate les arguments pour l'affichage dans le journal."""
    parties = [repr(a) for a in args]
    parties += [f"{k}={v!r}" for k, v in kwargs.items()]
    return ", ".join(parties)
