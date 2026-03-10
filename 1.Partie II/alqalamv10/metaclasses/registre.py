# [V6 - Métaclasses] RegistreMouvementMeta — enregistrement automatique des sous-classes.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  CONCEPT : Métaclasse Registre                                          │
# │                                                                         │
# │  Quand Python rencontre la définition d'une classe :                   │
# │    class EntreeMouvement(Mouvement):                                    │
# │        ...                                                              │
# │                                                                         │
# │  Il appelle la métaclasse de Mouvement pour créer EntreeMouvement.     │
# │  RegistreMouvementMeta.__init__() est appelée avec :                   │
# │    - nom       = "EntreeMouvement"                                      │
# │    - bases     = (Mouvement,)                                           │
# │    - namespace = {"TYPE_MVT": "entree", "ICONE": "📥", ...}            │
# │                                                                         │
# │  → La métaclasse lit TYPE_MVT dans namespace et enregistre la classe.  │
# │  → Aucun code supplémentaire n'est nécessaire dans la sous-classe !    │
# └─────────────────────────────────────────────────────────────────────────┘
#
# Avantage pédagogique :
#   Ajouter un nouveau type de mouvement = créer une sous-classe avec TYPE_MVT.
#   Le reste (registre, factory, UI) se met à jour AUTOMATIQUEMENT.


class RegistreMouvementMeta(type):
    """
    Métaclasse Registre — toute sous-classe de Mouvement s'enregistre automatiquement.

    Le registre associe une clé string (type_mvt) à la classe Python correspondante :
        {"entree": EntreeMouvement, "sortie": SortieMouvement, ...}

    Accès au registre :
        RegistreMouvementMeta.get_registre()    → dict complet
        RegistreMouvementMeta.get_classe("entree") → EntreeMouvement
        RegistreMouvementMeta.types_connus()    → ["entree", "sortie", ...]
    """

    # Dictionnaire partagé par toutes les classes utilisant cette métaclasse
    # Clé : type_mvt (str)  →  Valeur : classe Python (type)
    _registre: dict = {}

    def __init__(cls, nom: str, bases: tuple, namespace: dict) -> None:
        """
        Appelée automatiquement par Python lors de la définition de toute classe
        dont la métaclasse est (ou hérite de) RegistreMouvementMeta.

        [V6] C'est ici que l'auto-enregistrement se produit :
          - 'nom'       : nom de la classe en cours de création ("EntreeMouvement")
          - 'bases'     : classes parentes ((Mouvement,))
          - 'namespace' : corps de la classe (dict des attributs définis)
        """
        # Délègue d'abord à type.__init__() pour créer la classe normalement
        super().__init__(nom, bases, namespace)

        # [V6] Auto-enregistrement : on lit TYPE_MVT dans le namespace de la classe.
        # Si TYPE_MVT est défini ET non-None → c'est une sous-classe concrète.
        # La classe de base Mouvement a TYPE_MVT = None → elle n'est pas enregistrée.
        type_mvt = namespace.get("TYPE_MVT")
        if type_mvt is not None:
            RegistreMouvementMeta._registre[type_mvt] = cls

    # ── API du registre ───────────────────────────────────────────────────

    @classmethod
    def get_registre(mcs) -> dict:
        """Retourne une copie du registre (type_mvt → classe)."""
        return dict(mcs._registre)

    @classmethod
    def get_classe(mcs, type_mvt: str):
        """
        Retourne la classe enregistrée pour type_mvt, ou None.

        Exemple :
            cls = RegistreMouvementMeta.get_classe("entree")
            # cls == EntreeMouvement
        """
        return mcs._registre.get(type_mvt)

    @classmethod
    def types_connus(mcs) -> list:
        """Retourne la liste triée des types de mouvement enregistrés."""
        return sorted(mcs._registre.keys())

    @classmethod
    def est_enregistre(mcs, type_mvt: str) -> bool:
        """Retourne True si ce type de mouvement est dans le registre."""
        return type_mvt in mcs._registre
