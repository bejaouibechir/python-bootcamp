# [V5 - Décorateurs] JournalService — stocke les entrées de journal générées
# par le décorateur @journaliser.
# [V6] Inchangé — le journal enregistre désormais aussi "ajustement" et "retour".

import threading
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class EntreeJournal:
    """
    Représente un enregistrement de journal pour une opération stock.

    @dataclass génère automatiquement __init__, __repr__, __eq__
    en se basant sur les annotations de type.
    """
    operation : str
    ref       : str
    details   : str
    succes    : bool
    erreur    : str      = ""
    duree_ms  : int      = 0
    timestamp : datetime = field(default_factory=datetime.now)

    def heure_formatee(self) -> str:
        return self.timestamp.strftime("%H:%M:%S")

    def date_formatee(self) -> str:
        return self.timestamp.strftime("%d/%m/%Y")

    def icone(self) -> str:
        if not self.succes:
            return "❌"
        icones = {
            "entree"      : "📥",
            "sortie"      : "📤",
            "ajout"       : "➕",
            "suppression" : "🗑️",
            "modification": "✏️",
            "ajustement"  : "⚖️",   # [V6] nouveau type
            "retour"      : "↩️",   # [V6] nouveau type
        }
        return icones.get(self.operation, "🔹")

    def label_operation(self) -> str:
        labels = {
            "entree"      : "Entrée stock",
            "sortie"      : "Sortie stock",
            "ajout"       : "Nouveau produit",
            "suppression" : "Suppression",
            "modification": "Modification",
            "ajustement"  : "Ajustement",   # [V6]
            "retour"      : "Retour fourn.", # [V6]
        }
        return labels.get(self.operation, self.operation.capitalize())


class JournalService:
    """
    Stocke et expose l'historique des opérations enregistrées par @journaliser.
    Thread-safe via Lock.
    """

    def __init__(self):
        self._entrees : list[EntreeJournal] = []
        self._lock    = threading.Lock()

    def enregistrer(self, operation: str, ref: str, details: str,
                    succes: bool, erreur: str = "", duree_ms: int = 0) -> None:
        entree = EntreeJournal(
            operation=operation, ref=ref, details=details,
            succes=succes, erreur=erreur, duree_ms=duree_ms,
        )
        with self._lock:
            self._entrees.append(entree)

    def get_entrees(self) -> list[EntreeJournal]:
        with self._lock:
            return list(self._entrees)

    def get_recentes(self, n: int = 50) -> list[EntreeJournal]:
        with self._lock:
            return list(reversed(self._entrees[-n:]))

    def get_erreurs(self) -> list[EntreeJournal]:
        with self._lock:
            return [e for e in self._entrees if not e.succes]

    def vider(self) -> None:
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
