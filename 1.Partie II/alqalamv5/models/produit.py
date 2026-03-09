# [V5 - Descripteurs] La classe Produit utilise maintenant des descripteurs
# pour valider automatiquement chaque attribut lors de l'affectation.
#
# Avant (V4) : la validation était dans __init__ avec des if / raise manuels.
# Après (V5) : les descripteurs interceptent toute affectation (y compris
#              produit.qte += 5 fait dans stock_service) et valident à la volée.
#
# Avantage : impossible de mettre un prix négatif ou un nom vide,
#            même en dehors des dialogues de l'UI.

from models.descripteurs import Positif, PositifEntier, NonVide


class Produit:
    """
    Représente un produit en stock dans la papeterie Al Qalam.

    [V5] Les attributs numériques (prix, qte, seuil) sont protégés par des
    descripteurs qui rejettent les valeurs négatives.
    Les attributs texte (ref, nom, categorie) rejettent les chaînes vides.
    """

    # ── Descripteurs de classe ────────────────────────────────────────────
    # [V5] Ces objets sont définis au niveau de la CLASSE (pas de l'instance).
    # Python les consulte automatiquement lors de toute lecture/écriture.
    ref        = NonVide()        # ex: "CRAY-001"  — chaîne non vide
    nom        = NonVide()        # ex: "Crayon HB" — chaîne non vide
    categorie  = NonVide()        # ex: "Écriture"  — chaîne non vide
    prix_achat = Positif()        # float ≥ 0
    prix_vente = Positif()        # float ≥ 0
    qte        = PositifEntier()  # int ≥ 0  (peut être 0 si rupture totale)
    seuil_min  = PositifEntier()  # int ≥ 0

    def __init__(self, ref: str, nom: str, categorie: str,
                 prix_achat: float, prix_vente: float,
                 qte: int = 0, seuil_min: int = 5):
        # [V5] Ces affectations passent par les descripteurs → validation auto.
        # Chaque ligne appelle descriptor.__set__(self, valeur).
        self.ref        = ref
        self.nom        = nom
        self.categorie  = categorie
        self.prix_achat = prix_achat
        self.prix_vente = prix_vente
        self.qte        = qte
        self.seuil_min  = seuil_min

    # ── Méthodes métier ───────────────────────────────────────────────────

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

    # ── Sérialisation ─────────────────────────────────────────────────────

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
        """Recrée un Produit depuis un dictionnaire (chargement JSON)."""
        return cls(**data)

    # ── Représentation ────────────────────────────────────────────────────

    def __str__(self) -> str:
        statut = "⚠️ ALERTE" if self.est_en_alerte() else "✅ OK"
        return f"[{self.ref}] {self.nom} | Qté: {self.qte} | {statut}"

    def __repr__(self) -> str:
        return f"Produit(ref={self.ref!r}, nom={self.nom!r}, qte={self.qte})"

    # ── Méthodes Magiques V2 ──────────────────────────────────────────────

    def __eq__(self, other) -> bool:
        if not isinstance(other, Produit):
            return NotImplemented
        return self.ref == other.ref

    def __lt__(self, other) -> bool:
        if not isinstance(other, Produit):
            return NotImplemented
        return self.nom.lower() < other.nom.lower()

    def __hash__(self) -> int:
        return hash(self.ref)
