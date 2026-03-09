# [V1 - POO] La classe Categorie représente une famille de produits.
# Ex : "Écriture", "Papier", "Coupe", etc.

class Categorie:
    """
    Représente une catégorie de produits dans la papeterie.

    Attributs:
        nom (str)        : nom de la catégorie
        description (str): description optionnelle
        icone (str)      : emoji représentatif
    """

    # [POO] Attribut de classe : partagé par toutes les instances
    CATEGORIES_DEFAUT = [
        ("Écriture",  "Crayons, stylos, feutres",       "✏️"),
        ("Papier",    "Rames, cahiers, carnets",          "📄"),
        ("Effaçage",  "Gommes, correcteurs",              "🧹"),
        ("Coupe",     "Ciseaux, cutters, règles",         "✂️"),
        ("Mesure",    "Règles, équerres, rapporteurs",   "📐"),
        ("Classement","Classeurs, chemises, reliures",    "📁"),
    ]

    def __init__(self, nom: str, description: str = "", icone: str = "📦"):
        self.nom         = nom
        self.description = description
        self.icone       = icone

    def __str__(self) -> str:
        return f"{self.icone} {self.nom}"

    def __repr__(self) -> str:
        return f"Categorie(nom={self.nom!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Categorie):
            return NotImplemented
        return self.nom.lower() == other.nom.lower()
