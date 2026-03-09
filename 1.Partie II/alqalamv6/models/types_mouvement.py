# [V6 - Métaclasses] Sous-classes concrètes de Mouvement.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  AUTO-ENREGISTREMENT                                                    │
# │                                                                         │
# │  Quand Python lit "class EntreeMouvement(Mouvement):", il appelle :    │
# │    RegistreMouvementMeta.__init__("EntreeMouvement", (Mouvement,), {...})│
# │                                                                         │
# │  La métaclasse lit TYPE_MVT = "entree" dans le namespace               │
# │  et exécute : RegistreMouvementMeta._registre["entree"] = EntreeMouvement│
# │                                                                         │
# │  Aucune ligne de code n'est nécessaire dans EntreeMouvement elle-même ! │
# └─────────────────────────────────────────────────────────────────────────┘
#
# IMPORTANT : importer ce module AVANT d'appeler Mouvement.fabriquer(),
# sinon les classes ne sont pas encore définies et le registre est vide.
# C'est pourquoi stock_service.py importe ce module au chargement.

from models.mouvement import Mouvement


# ── Type 1 : Entrée de stock ───────────────────────────────────────────────

class EntreeMouvement(Mouvement):
    """
    Mouvement d'entrée — réception de marchandise fournisseur.

    [V6] TYPE_MVT = "entree" → enregistrement automatique dans le registre
         lors de la définition de cette classe par Python.

    Simplification de l'interface :
        EntreeMouvement(ref, qte, note)
        → appelle Mouvement.__init__(ref, "entree", qte, note)
    """
    # [V6] Cet attribut déclenche l'auto-enregistrement par RegistreMouvementMeta
    TYPE_MVT = "entree"
    ICONE    = "📥"
    LABEL    = "Entrée stock"

    def __init__(self, ref_produit: str, qte: int, note: str = ""):
        # Délègue à la classe de base avec le type_mvt fixe
        super().__init__(ref_produit, "entree", qte, note)


# ── Type 2 : Sortie de stock ───────────────────────────────────────────────

class SortieMouvement(Mouvement):
    """
    Mouvement de sortie — vente ou consommation interne.

    [V6] TYPE_MVT = "sortie" → auto-enregistrement identique.
    """
    TYPE_MVT = "sortie"
    ICONE    = "📤"
    LABEL    = "Sortie stock"

    def __init__(self, ref_produit: str, qte: int, note: str = ""):
        super().__init__(ref_produit, "sortie", qte, note)


# ── Type 3 : Ajustement d'inventaire ──────────────────────────────────────

class AjustementMouvement(Mouvement):
    """
    Ajustement d'inventaire physique — correction de l'écart entre
    stock théorique et stock réel (casse, perte, comptage manuel).

    [V6] Nouveau type introduit en V6 pour illustrer l'extensibilité du registre.
         Ajouter ce type n'a nécessité aucune modification dans StockService :
         la factory Mouvement.fabriquer("ajustement", ...) le gère automatiquement.

    Attribut supplémentaire :
        delta (int) : écart constaté (positif = gain, négatif = perte)
    """
    TYPE_MVT = "ajustement"
    ICONE    = "⚖️"
    LABEL    = "Ajustement"

    def __init__(self, ref_produit: str, qte: int, note: str = ""):
        # qte = valeur absolue de l'écart (toujours positive pour Mouvement.__init__)
        super().__init__(ref_produit, "ajustement", abs(qte) if qte != 0 else 1, note)
        # delta stocké séparément (peut être négatif pour indiquer une perte)
        self.delta = qte


# ── Type 4 : Retour fournisseur ────────────────────────────────────────────

class RetourMouvement(Mouvement):
    """
    Retour fournisseur — marchandise renvoyée (défaut qualité, surplus).

    [V6] Quatrième type enregistré automatiquement.
    Fonctionnellement similaire à une sortie, mais catégorisé séparément
    pour les rapports comptables.
    """
    TYPE_MVT = "retour"
    ICONE    = "↩️"
    LABEL    = "Retour fournisseur"

    def __init__(self, ref_produit: str, qte: int, note: str = ""):
        super().__init__(ref_produit, "retour", qte, note)
