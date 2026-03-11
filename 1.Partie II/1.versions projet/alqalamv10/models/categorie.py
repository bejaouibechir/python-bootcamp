# [V1 - POO] La classe Categorie représente une famille de produits.

class Categorie:
    """Représente une catégorie de produits (Écriture, Papier, etc.)."""

    def __init__(self, nom: str, description: str = ""):
        self.nom         = nom
        self.description = description

    def __str__(self) -> str:
        return self.nom

    def __repr__(self) -> str:
        return f"Categorie(nom={self.nom!r})"
