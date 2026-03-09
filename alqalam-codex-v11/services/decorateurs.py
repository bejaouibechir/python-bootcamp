"""Décorateurs métier pour validation, logs et chronométrage."""

from __future__ import annotations

import functools
import logging
import time

logger = logging.getLogger(__name__)


def valider_quantite(func):
    """Vérifie que la quantité est un entier strictement positif."""

    @functools.wraps(func)
    def wrapper(self, ref, qte, *args, **kwargs):
        if not isinstance(qte, int):
            raise TypeError(f"La quantité doit être un entier, reçu : {type(qte).__name__}")
        if qte <= 0:
            raise ValueError(f"La quantité doit être positive, reçu : {qte}")
        return func(self, ref, qte, *args, **kwargs)

    return wrapper


def logger_operation(func):
    """Trace automatiquement succès/erreur des opérations de stock."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(self, *args, **kwargs)
            ms = (time.perf_counter() - start) * 1000
            logger.info("✅ %s args=%s %.2fms", func.__name__, args, ms)
            return result
        except Exception as exc:
            logger.error("❌ %s args=%s erreur=%s", func.__name__, args, exc)
            raise

    return wrapper


def chrono(func):
    """Affiche le temps d'exécution d'une fonction."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"⏱ {func.__name__} exécuté en {(end - start) * 1000:.2f} ms")
        return result

    return wrapper
