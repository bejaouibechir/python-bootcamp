# [V6 - Métaclasses] Mouvement utilise RegistreMouvementMeta comme métaclasse.
#
# Avant (V1→V5) : class Mouvement:  → métaclasse implicite = type
# Après  (V6)   : class Mouvement(metaclass=RegistreMouvementMeta):
#                   → chaque sous-classe s'enregistre automatiquement !
#
# Nouvelle fonctionnalité V6 :
#   Mouvement.fabriquer("entree", ref, qte, note)
#   → consulte le registre → crée EntreeMouvement(ref, qte, note)
#   → si le type est inconnu, crée un Mouvement de base (fallback)
#
# Types valides étendus :
#   V1–V5 : "entree", "sortie"
#   V6    : + "ajustement" (inventaire physique), + "retour" (retour fournisseur)

from datetime import datetime
from metaclasses.registre import RegistreMouvementMeta


class Mouvement(metaclass=RegistreMouvementMeta):
    """
    Représente un mouvement de stock (entrée, sortie, ajustement, retour).

    [V6] Cette classe utilise RegistreMouvementMeta comme métaclasse.
    Cela signifie que :
      - Toute sous-classe avec TYPE_MVT défini s'enregistre automatiquement.
      - La méthode de classe fabriquer() peut créer le bon type via le registre.
      - type(Mouvement) retourne RegistreMouvementMeta (pas type !).

    Attributs de classe (pour les sous-classes) :
      TYPE_MVT (str|None) : identifiant du type — None sur la classe de base
      ICONE    (str)      : emoji affiché dans l'UI
      LABEL    (str)      : libellé lisible
    """

    # [V6] TYPE_MVT = None → la classe de base n'est PAS enregistrée dans le registre.
    # Les sous-classes définissent TYPE_MVT = "entree" etc. pour s'enregistrer.
    TYPE_MVT = None
    ICONE    = "🔹"
    LABEL    = "Mouvement"

    # Types acceptés par __init__ (étendu en V6 pour couvrir les sous-classes)
    TYPES_VALIDES = ("entree", "sortie", "ajustement", "retour")

    def __init__(self, ref_produit: str, type_mvt: str, qte: int, note: str = ""):
        # [POO] Validation dans __init__ : l'objet naît toujours dans un état valide
        if type_mvt not in self.TYPES_VALIDES:
            raise ValueError(
                f"Type de mouvement invalide : {type_mvt!r}. "
                f"Attendu : {self.TYPES_VALIDES}"
            )
        if qte <= 0:
            raise ValueError(f"La quantité doit être positive, reçu : {qte}")

        self.ref_produit = ref_produit
        self.type_mvt    = type_mvt
        self.qte         = qte
        self.note        = note
        self.date        = datetime.now().isoformat(timespec="seconds")

    # ── Factory V6 ────────────────────────────────────────────────────────

    @classmethod
    def fabriquer(cls, type_mvt: str, ref_produit: str,
                  qte: int, note: str = "") -> "Mouvement":
        """
        [V6] Fabrique le bon type de mouvement en consultant le registre.

        Principe :
          type(cls) == RegistreMouvementMeta  (la métaclasse de Mouvement)
          On lit son _registre pour trouver la classe correspondant à type_mvt.

        Exemple :
          Mouvement.fabriquer("entree", "CRAY-001", 50)
          → registre["entree"] == EntreeMouvement
          → EntreeMouvement("CRAY-001", 50)

        Fallback :
          Si type_mvt n'est pas dans le registre (types ajoutés dynamiquement),
          on instancie la classe de base Mouvement directement.
        """
        # type(cls) retourne la métaclasse : RegistreMouvementMeta
        # On accède à _registre directement sur la métaclasse
        meta = type(cls)
        classe = meta.get_classe(type_mvt)

        if classe is not None:
            # La sous-classe concrète gère elle-même type_mvt dans son __init__
            return classe(ref_produit, qte, note)

        # Fallback : type inconnu → Mouvement de base
        return cls(ref_produit, type_mvt, qte, note)

    # ── Méthodes métier ───────────────────────────────────────────────────

    def est_entree(self) -> bool:
        """Retourne True si c'est un mouvement entrant (stock qui monte)."""
        return self.type_mvt in ("entree", "retour")

    def est_sortie(self) -> bool:
        """Retourne True si c'est un mouvement sortant (stock qui descend)."""
        return self.type_mvt == "sortie"

    def est_ajustement(self) -> bool:
        """Retourne True si c'est un ajustement d'inventaire."""
        return self.type_mvt == "ajustement"

    def icone_affichage(self) -> str:
        """Retourne l'icône de la classe concrète (ou défaut)."""
        # Pour la classe de base, on lit ICONE sur la classe de l'instance
        return type(self).ICONE

    def label_affichage(self) -> str:
        """Retourne le label lisible de la classe concrète."""
        return type(self).LABEL

    # ── Sérialisation ─────────────────────────────────────────────────────

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
        icone = self.icone_affichage()
        return f"[{self.date[:10]}] {icone} {self.label_affichage()} {self.qte}× {self.ref_produit} — {self.note or '—'}"

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(ref={self.ref_produit!r}, "
                f"type={self.type_mvt!r}, qte={self.qte})")
