"""Modèle métier Produit."""

from __future__ import annotations


class QuantitePositive:
    """Descripteur qui impose une quantité entière >= 0."""

    def __set_name__(self, owner, name):
        self._name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._name, 0)

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError("La quantité doit être un entier")
        if value < 0:
            raise ValueError(f"La quantité ne peut pas être négative : {value}")
        setattr(instance, self._name, value)


class Produit:
    """Représente un produit de la papeterie."""

    qte = QuantitePositive()

    def __init__(
        self,
        ref: str,
        nom: str,
        categorie: str,
        prix_achat: float,
        prix_vente: float,
        qte: int = 0,
        seuil_min: int = 5,
        date_ajout: str | None = None,
        date_modif: str | None = None,
    ):
        self.ref = ref.strip().upper()
        self.nom = nom.strip()
        self.categorie = categorie.strip()
        self.prix_achat = float(prix_achat)
        self.prix_vente = float(prix_vente)
        self.qte = int(qte)
        self.seuil_min = int(seuil_min)
        self.date_ajout = date_ajout
        self.date_modif = date_modif

    def est_en_alerte(self) -> bool:
        return self.qte <= self.seuil_min

    def valeur_stock(self) -> float:
        return self.qte * self.prix_achat

    def marge_unitaire(self) -> float:
        return self.prix_vente - self.prix_achat

    def to_dict(self) -> dict:
        return {
            "ref": self.ref,
            "nom": self.nom,
            "categorie": self.categorie,
            "prix_achat": self.prix_achat,
            "prix_vente": self.prix_vente,
            "qte": self.qte,
            "seuil_min": self.seuil_min,
            "date_ajout": self.date_ajout,
            "date_modif": self.date_modif,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Produit":
        return cls(**data)

    def __str__(self):
        statut = "⚠️ ALERTE" if self.est_en_alerte() else "✅ OK"
        return f"[{self.ref}] {self.nom} | Qté: {self.qte} | {statut}"

    def __repr__(self):
        return f"Produit(ref={self.ref!r}, nom={self.nom!r}, qte={self.qte})"

    def __eq__(self, other):
        if not isinstance(other, Produit):
            return NotImplemented
        return self.ref == other.ref

    def __lt__(self, other):
        if not isinstance(other, Produit):
            return NotImplemented
        return self.nom.lower() < other.nom.lower()

    def __hash__(self):
        return hash(self.ref)
