# [V5 - Décorateurs] JournalService — stocke les entrées de journal générées
# par le décorateur @journaliser.
#
# Ce service est créé par StockService et passé implicitement au décorateur
# via self._journal. Il est thread-safe (V4 Lock) car les méthodes décorées
# de StockService peuvent être appelées depuis plusieurs threads.

import threading
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class EntreeJournal:
    """
    Représente un enregistrement de journal pour une opération stock.

    [V5] @dataclass génère automatiquement __init__, __repr__, __eq__
    en se basant sur les annotations de type. Pas besoin d'écrire ces
    méthodes manuellement.
    """
    operation : str                          # "entree", "sortie", "ajout"…
    ref       : str                          # référence du produit concerné
    details   : str                          # arguments formatés
    succes    : bool                         # True = pas d'exception levée
    erreur    : str   = ""                   # message d'erreur si succes=False
    duree_ms  : int   = 0                    # durée d'exécution en millisecondes
    timestamp : datetime = field(            # heure automatique
        default_factory=datetime.now
    )

    def heure_formatee(self) -> str:
        """Retourne l'heure au format lisible HH:MM:SS."""
        return self.timestamp.strftime("%H:%M:%S")

    def date_formatee(self) -> str:
        """Retourne la date au format DD/MM/YYYY."""
        return self.timestamp.strftime("%d/%m/%Y")

    def icone(self) -> str:
        """Icône visuelle selon le succès et le type d'opération."""
        if not self.succes:
            return "❌"
        icones = {
            "entree"   : "📥",
            "sortie"   : "📤",
            "ajout"    : "➕",
            "suppression": "🗑️",
            "modification": "✏️",
        }
        return icones.get(self.operation, "🔹")

    def label_operation(self) -> str:
        """Libellé lisible de l'opération."""
        labels = {
            "entree"     : "Entrée stock",
            "sortie"     : "Sortie stock",
            "ajout"      : "Nouveau produit",
            "suppression": "Suppression",
            "modification": "Modification",
        }
        return labels.get(self.operation, self.operation.capitalize())


class JournalService:
    """
    Stocke et expose l'historique des opérations enregistrées par @journaliser.

    Thread-safe : utilise un Lock hérité de V4 car StockService peut être
    accédé depuis le thread de surveillance.
    """

    def __init__(self):
        self._entrees : list[EntreeJournal] = []
        self._lock    = threading.Lock()

    def enregistrer(self, operation: str, ref: str, details: str,
                    succes: bool, erreur: str = "", duree_ms: int = 0) -> None:
        """Ajoute une nouvelle entrée dans le journal (thread-safe)."""
        entree = EntreeJournal(
            operation = operation,
            ref       = ref,
            details   = details,
            succes    = succes,
            erreur    = erreur,
            duree_ms  = duree_ms,
        )
        with self._lock:
            self._entrees.append(entree)

    def get_entrees(self) -> list[EntreeJournal]:
        """Retourne une copie thread-safe de toutes les entrées."""
        with self._lock:
            return list(self._entrees)

    def get_recentes(self, n: int = 50) -> list[EntreeJournal]:
        """Retourne les N dernières entrées (les plus récentes en premier)."""
        with self._lock:
            return list(reversed(self._entrees[-n:]))

    def get_erreurs(self) -> list[EntreeJournal]:
        """Retourne uniquement les opérations ayant échoué."""
        with self._lock:
            return [e for e in self._entrees if not e.succes]

    def vider(self) -> None:
        """Efface tout le journal."""
        with self._lock:
            self._entrees.clear()

    @property
    def nb_total(self) -> int:
        with self._lock:
            return len(self._entrees)

    @property
    def nb_erreurs(self) -> int:
        with self._lock:
            return sum(1 for e in self._entrees if not e.succes)
