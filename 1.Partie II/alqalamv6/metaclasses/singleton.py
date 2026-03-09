# [V6 - Métaclasses] SingletonMeta — garantit une unique instance par classe.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  CONCEPT : Métaclasse Singleton                                         │
# │                                                                         │
# │  Normalement, MonObjet() appelle :                                      │
# │    1. type.__call__(MonObjet)     ← la métaclasse gère l'appel         │
# │    2.   MonObjet.__new__(cls)     ← alloue la mémoire                  │
# │    3.   MonObjet.__init__(self)   ← initialise l'objet                 │
# │                                                                         │
# │  SingletonMeta surcharge __call__() :                                   │
# │    - Si instance déjà créée → retourne l'instance existante             │
# │    - Sinon → délègue à super().__call__() (chemin normal)               │
# │                                                                         │
# │  Résultat : StockService() is StockService()  →  True                  │
# └─────────────────────────────────────────────────────────────────────────┘
#
# Pourquoi une métaclasse plutôt qu'un module-level ou un décorateur ?
#   → La métaclasse contrôle la création à un niveau plus fondamental.
#   → Toute sous-classe de StockService hérite automatiquement du comportement.
#   → C'est le mécanisme idiomatique Python pour des Singletons hérités.

import threading


class SingletonMeta(type):
    """
    Métaclasse Singleton — une seule instance par classe garantie par métaclasse.

    Utilisation :
        class StockService(metaclass=SingletonMeta):
            ...

        a = StockService()
        b = StockService()
        assert a is b   # True — même objet en mémoire
        assert id(a) == id(b)

    Thread-safety :
        Un Lock est utilisé pour éviter les conditions de concurrence lors
        de la première création si deux threads appellent StockService()
        simultanément.
    """

    # Dictionnaire de classe → instance unique
    # (attribut de la métaclasse, partagé entre toutes les classes qui l'utilisent)
    _instances: dict = {}

    # Verrou pour la création thread-safe de la première instance
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """
        Intercepte chaque appel à MaClasse(*args, **kwargs).

        [V6] C'est ici que la magie opère :
          - type.__call__(cls) crée normalement une nouvelle instance à chaque appel.
          - SingletonMeta.__call__() vérifie d'abord si une instance existe déjà.

        Le double-check locking (vérification avant ET après le Lock) évite
        le problème de performance d'un Lock systématique sur chaque appel.
        """
        # Vérification rapide SANS Lock (chemin nominal une fois l'instance créée)
        if cls not in SingletonMeta._instances:
            with SingletonMeta._lock:
                # Vérification à nouveau AVEC Lock (en cas de race condition)
                if cls not in SingletonMeta._instances:
                    # super().__call__() → appelle type.__call__()
                    #   → appelle cls.__new__(cls)  + cls.__init__(instance)
                    instance = super().__call__(*args, **kwargs)
                    SingletonMeta._instances[cls] = instance

        return SingletonMeta._instances[cls]

    @classmethod
    def _reset(mcs, cls=None) -> None:
        """
        Réinitialise le registre Singleton (utile pour les tests unitaires).
        Si cls=None, réinitialise toutes les classes. Sinon, réinitialise cls seule.
        """
        if cls is None:
            mcs._instances.clear()
        elif cls in mcs._instances:
            del mcs._instances[cls]

    @classmethod
    def get_instances(mcs) -> dict:
        """Retourne une copie du registre des instances (pour l'UI pédagogique)."""
        return dict(mcs._instances)
