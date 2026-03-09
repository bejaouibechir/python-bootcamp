"""Modèle simple pour les catégories."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Categorie:
    """Structure simple pour représenter une catégorie de produits."""

    nom: str
    description: str = ""
