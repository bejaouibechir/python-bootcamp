# [V1 - POO] La classe Mouvement enregistre chaque opération de stock.
# C'est l'historique : qui a fait quoi, quand, et combien.

from datetime import datetime


class Mouvement:
    """
    Représente un mouvement de stock (entrée ou sortie).

    Attributs:
        ref_produit (str) : référence du produit concerné
        type_mvt (str)    : "entree" ou "sortie"
        qte (int)         : quantité déplacée
        note (str)        : commentaire optionnel
        date (str)        : horodatage ISO 8601 (généré automatiquement)
    """

    # Types de mouvement autorisés (V6 les étendra avec métaclasses)
    TYPES_VALIDES = ("entree", "sortie")

    def __init__(self, ref_produit: str, type_mvt: str, qte: int, note: str = ""):
        # [POO] Validation dans __init__ : l'objet naît toujours dans un état valide
        if type_mvt not in self.TYPES_VALIDES:
            raise ValueError(f"Type de mouvement invalide : {type_mvt!r}. "
                             f"Attendu : {self.TYPES_VALIDES}")
        if qte <= 0:
            raise ValueError(f"La quantité doit être positive, reçu : {qte}")

        self.ref_produit = ref_produit
        self.type_mvt    = type_mvt
        self.qte         = qte
        self.note        = note
        # datetime.now() capture l'heure exacte de l'opération
        self.date        = datetime.now().isoformat(timespec="seconds")

    def est_entree(self) -> bool:
        """Retourne True si c'est une entrée de stock."""
        return self.type_mvt == "entree"

    def est_sortie(self) -> bool:
        """Retourne True si c'est une sortie de stock."""
        return self.type_mvt == "sortie"

    def to_dict(self) -> dict:
        """Convertit le mouvement en dictionnaire (pour sauvegarde)."""
        return {
            "ref_produit": self.ref_produit,
            "type_mvt"   : self.type_mvt,
            "qte"        : self.qte,
            "note"       : self.note,
            "date"       : self.date,
        }

    def __str__(self) -> str:
        direction = "↑ Entrée" if self.est_entree() else "↓ Sortie"
        return f"[{self.date[:10]}] {direction} {self.qte}× {self.ref_produit} — {self.note or '—'}"

    def __repr__(self) -> str:
        return f"Mouvement(ref={self.ref_produit!r}, type={self.type_mvt!r}, qte={self.qte})"
