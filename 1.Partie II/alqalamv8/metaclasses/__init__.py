# [V6 - Métaclasses] Package metaclasses — outils de méta-programmation Python.
#
# Une métaclasse est la "classe d'une classe" : elle contrôle comment les
# classes elles-mêmes sont créées, modifiées et instanciées.
#
# Analogie :
#   Classe normale → fabrique d'objets  (Produit() crée un objet Produit)
#   Métaclasse     → fabrique de classes (SingletonMeta contrôle Produit lui-même)
#
# Ce package contient :
#   singleton.py  → SingletonMeta  : une seule instance par classe garantie
#   registre.py   → RegistreMouvementMeta : auto-enregistrement des sous-classes
