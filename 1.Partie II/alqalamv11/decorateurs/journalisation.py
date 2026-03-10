# [V5 - Décorateurs] Décorateur de journalisation automatique — inchangé en V6.

import functools
from datetime import datetime


def journaliser(operation: str):
    """
    Fabrique de décorateurs — enregistre automatiquement chaque opération
    dans le JournalService de l'instance StockService.
    """
    def decorateur(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
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
                raise
            finally:
                duree_ms = int((datetime.now() - debut).total_seconds() * 1000)
                if hasattr(self, "_journal"):
                    self._journal.enregistrer(
                        operation=operation,
                        ref=ref,
                        details=_formater_args(args, kwargs),
                        succes=succes,
                        erreur=erreur or "",
                        duree_ms=duree_ms,
                    )
        return wrapper
    return decorateur


def _formater_args(args: tuple, kwargs: dict) -> str:
    parties = [repr(a) for a in args]
    parties += [f"{k}={v!r}" for k, v in kwargs.items()]
    return ", ".join(parties)
