"""Modèles des mouvements de stock avec registre automatique."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar


@dataclass
class Mouvement:
    """Classe de base des mouvements de stock."""

    ref_produit: str
    qte: int
    qte_avant: int
    qte_apres: int
    note: str = ""
    date_mvt: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    _registre: ClassVar[dict[str, type["Mouvement"]]] = {}
    TYPE = "inconnu"

    def __init_subclass__(cls, type_mvt: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if type_mvt:
            cls.TYPE = type_mvt
            Mouvement._registre[type_mvt] = cls

    @classmethod
    def creer(cls, type_mvt: str, **kwargs) -> "Mouvement":
        if type_mvt not in cls._registre:
            raise ValueError(f"Type inconnu : {type_mvt}")
        return cls._registre[type_mvt](**kwargs)

    @classmethod
    def types_disponibles(cls) -> list[str]:
        return list(cls._registre.keys())

    def to_dict(self) -> dict:
        return {
            "ref_produit": self.ref_produit,
            "type_mvt": self.TYPE,
            "qte": self.qte,
            "qte_avant": self.qte_avant,
            "qte_apres": self.qte_apres,
            "note": self.note,
            "date_mvt": self.date_mvt,
        }

    def __str__(self):
        return f"{self.date_mvt} | {self.TYPE} | {self.ref_produit} | {self.qte}"

    def __lt__(self, other):
        if not isinstance(other, Mouvement):
            return NotImplemented
        return self.date_mvt < other.date_mvt


class MouvementEntree(Mouvement, type_mvt="entree"):
    """Mouvement d'entrée."""


class MouvementSortie(Mouvement, type_mvt="sortie"):
    """Mouvement de sortie."""


class MouvementRetour(Mouvement, type_mvt="retour"):
    """Mouvement de retour."""


class MouvementInventaire(Mouvement, type_mvt="inventaire"):
    """Mouvement de correction inventaire."""
