# [V1 - POO] La classe Produit est le cœur du logiciel.
# Elle regroupe toutes les informations d'un produit en un seul objet.
# Un "objet" = données (attributs) + comportements (méthodes).

class Produit:
    """
    Représente un produit en stock dans la papeterie Al Qalam.

    Attributs:
        ref (str)         : référence unique ex: CRAY-001
        nom (str)         : nom du produit
        categorie (str)   : famille du produit
        prix_achat (float): prix d'achat fournisseur (en TND)
        prix_vente (float): prix de vente client (en TND)
        qte (int)         : quantité actuelle en stock
        seuil_min (int)   : quantité minimale avant alerte de rupture
    """

    def __init__(self, ref: str, nom: str, categorie: str,
                 prix_achat: float, prix_vente: float,
                 qte: int = 0, seuil_min: int = 5):
        # [POO] __init__ est appelé automatiquement à la création de l'objet.
        # 'self' désigne l'objet en cours de création.
        self.ref        = ref
        self.nom        = nom
        self.categorie  = categorie
        self.prix_achat = float(prix_achat)
        self.prix_vente = float(prix_vente)
        self.qte        = int(qte)
        self.seuil_min  = int(seuil_min)

    # ── Méthodes métier ───────────────────────────────────────────────────
    # Ces méthodes encapsulent des règles métier : la logique est dans l'objet,
    # pas dispersée dans tout le programme.

    def est_en_alerte(self) -> bool:
        """Retourne True si la quantité est sous le seuil minimum."""
        return self.qte <= self.seuil_min

    def valeur_stock(self) -> float:
        """Valeur totale du stock pour ce produit (qte × prix_achat)."""
        return self.qte * self.prix_achat

    def marge_unitaire(self) -> float:
        """Bénéfice potentiel par unité vendue."""
        return self.prix_vente - self.prix_achat

    def statut_label(self) -> str:
        """Retourne une étiquette lisible du statut de stock."""
        return "⚠️ Alerte" if self.est_en_alerte() else "✅ OK"

    # ── Sérialisation ────────────────────────────────────────────────────
    # Ces méthodes permettent de convertir l'objet en dictionnaire
    # pour le sauvegarder dans un fichier JSON, et de le recréer.

    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire (pour sauvegarde JSON)."""
        return {
            "ref"       : self.ref,
            "nom"       : self.nom,
            "categorie" : self.categorie,
            "prix_achat": self.prix_achat,
            "prix_vente": self.prix_vente,
            "qte"       : self.qte,
            "seuil_min" : self.seuil_min,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Produit":
        """
        Recrée un objet Produit depuis un dictionnaire (chargement JSON).

        [POO] @classmethod reçoit la classe (cls) plutôt que l'instance (self).
        Il sert de constructeur alternatif — ici pour charger depuis JSON.
        """
        return cls(**data)

    def __str__(self) -> str:
        """Représentation lisible — appelée par print(produit)."""
        return f"[{self.ref}] {self.nom} | Qté: {self.qte} | {self.statut_label()}"

    def __repr__(self) -> str:
        """Représentation technique — utile dans le débogueur."""
        return f"Produit(ref={self.ref!r}, nom={self.nom!r}, qte={self.qte})"
