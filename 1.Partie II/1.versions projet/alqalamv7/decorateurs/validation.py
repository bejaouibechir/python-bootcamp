# [V5 - Décorateurs] Décorateurs de validation — inchangés en V6.

import functools
import time


def chronometre(func):
    """Décorateur simple — mesure la durée d'exécution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        debut    = time.perf_counter()
        resultat = func(*args, **kwargs)
        fin      = time.perf_counter()
        print(f"[⏱ chrono] {func.__qualname__}  →  {(fin-debut)*1000:.2f} ms")
        return resultat
    return wrapper


def valider_qte(min_val: int = 1, max_val: int = 100_000):
    """Fabrique de décorateur — valide la quantité passée en 2e argument."""
    def decorateur(func):
        @functools.wraps(func)
        def wrapper(self, ref, qte, *args, **kwargs):
            if not isinstance(qte, int):
                raise TypeError(
                    f"[{func.__name__}] La quantité doit être un entier, "
                    f"reçu : {type(qte).__name__}"
                )
            if not (min_val <= qte <= max_val):
                raise ValueError(
                    f"[{func.__name__}] Quantité hors plage "
                    f"({min_val}–{max_val}), reçu : {qte}"
                )
            return func(self, ref, qte, *args, **kwargs)
        return wrapper
    return decorateur


def valider_ref(func):
    """Décorateur simple — vérifie que la référence est une chaîne non vide."""
    @functools.wraps(func)
    def wrapper(self, ref, *args, **kwargs):
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError(
                f"[{func.__name__}] La référence doit être une chaîne non vide, "
                f"reçu : {ref!r}"
            )
        return func(self, ref.strip().upper(), *args, **kwargs)
    return wrapper
