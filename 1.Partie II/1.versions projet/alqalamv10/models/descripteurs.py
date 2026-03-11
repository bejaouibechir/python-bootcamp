# [V5 - Descripteurs] Protocole descripteur Python.
#
# Un descripteur est un objet qui contrôle l'accès à un attribut d'une autre classe.
# Il implémente au moins une des méthodes : __get__, __set__, __delete__.
#
# Protocole :
#   __set_name__(owner, name)  → appelé quand la classe est définie (Python 3.6+)
#   __get__(obj, objtype)      → appelé lors de la LECTURE  : produit.prix_achat
#   __set__(obj, valeur)       → appelé lors de l'ÉCRITURE  : produit.prix_achat = 1.5
#   __delete__(obj)            → appelé lors de la SUPPRESSION : del produit.prix_achat
#
# Différence descripteur / property :
#   @property  → descripteur pour UNE seule instance d'attribut (un nom fixe)
#   Descripteur → réutilisable : on peut l'appliquer à N attributs de N classes


class Positif:
    """
    Descripteur de données — garantit qu'un attribut numérique est ≥ 0.
    Réutilisé pour prix_achat, prix_vente, qte, seuil_min de Produit.

    Descripteur de DONNÉES (implémente __set__) → priorité sur __dict__ de l'instance.
    """

    def __set_name__(self, owner, name: str) -> None:
        """
        Appelé automatiquement par Python quand la classe est construite.
        'owner' = la classe (Produit), 'name' = le nom de l'attribut.
        On stocke la valeur dans '_prix_achat', '_qte'… pour éviter la récursion.
        """
        self._nom_public = name          # "prix_achat"
        self._nom_prive  = f"_{name}"   # "_prix_achat"  ← stockage réel

    def __get__(self, obj, objtype=None):
        """
        Appelé à la LECTURE : produit.prix_achat
        obj=None quand on accède via la classe (Produit.prix_achat) → on retourne
        le descripteur lui-même (convention Python).
        """
        if obj is None:
            return self   # accès depuis la classe : Produit.prix_achat → <Positif>
        return getattr(obj, self._nom_prive, 0)

    def __set__(self, obj, valeur) -> None:
        """
        Appelé à l'ÉCRITURE : produit.prix_achat = 1.5
        Valide, convertit, puis stocke dans l'attribut privé.
        """
        # Coercion de type
        try:
            valeur = float(valeur)
        except (TypeError, ValueError):
            raise TypeError(
                f"'{self._nom_public}' doit être numérique, reçu : {type(valeur).__name__}"
            )
        # Validation
        if valeur < 0:
            raise ValueError(
                f"'{self._nom_public}' doit être ≥ 0, reçu : {valeur}"
            )
        setattr(obj, self._nom_prive, valeur)


class PositifEntier(Positif):
    """
    Descripteur spécialisé pour les attributs entiers ≥ 0 (qte, seuil_min).
    Hérite de Positif et surcharge uniquement la coercion de type.
    """

    def __set__(self, obj, valeur) -> None:
        try:
            valeur = int(valeur)
        except (TypeError, ValueError):
            raise TypeError(
                f"'{self._nom_public}' doit être un entier, reçu : {type(valeur).__name__}"
            )
        if valeur < 0:
            raise ValueError(
                f"'{self._nom_public}' doit être ≥ 0, reçu : {valeur}"
            )
        setattr(obj, self._nom_prive, valeur)


class NonVide:
    """
    Descripteur de données — garantit qu'un attribut chaîne est non vide.
    Réutilisé pour ref, nom, categorie de Produit.
    """

    def __set_name__(self, owner, name: str) -> None:
        self._nom_public = name
        self._nom_prive  = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._nom_prive, "")

    def __set__(self, obj, valeur) -> None:
        if not isinstance(valeur, str):
            raise TypeError(
                f"'{self._nom_public}' doit être une chaîne, reçu : {type(valeur).__name__}"
            )
        valeur = valeur.strip()
        if not valeur:
            raise ValueError(f"'{self._nom_public}' ne peut pas être vide.")
        setattr(obj, self._nom_prive, valeur)
