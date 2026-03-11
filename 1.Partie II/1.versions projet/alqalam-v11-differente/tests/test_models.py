from __future__ import annotations

import pytest

from models.mouvement import Mouvement
from models.produit import Produit


def test_produit_est_en_alerte_true():
    assert Produit("A-001", "A", "Cat", 1, 2, 1, 2).est_en_alerte() is True


def test_produit_est_en_alerte_false():
    assert Produit("A-001", "A", "Cat", 1, 2, 10, 2).est_en_alerte() is False


def test_valeur_stock():
    p = Produit("A-001", "A", "Cat", 2.5, 3, 4, 1)
    assert p.valeur_stock() == 10


def test_marge_unitaire():
    p = Produit("A-001", "A", "Cat", 2.5, 5, 4, 1)
    assert p.marge_unitaire() == 2.5


def test_to_dict_from_dict():
    p = Produit("A-001", "A", "Cat", 1, 2, 3, 4)
    clone = Produit.from_dict(p.to_dict())
    assert clone == p
    assert clone.qte == 3


def test_eq_sur_ref():
    p1 = Produit("A-001", "AAA", "Cat", 1, 2)
    p2 = Produit("A-001", "BBB", "Cat", 1, 2)
    assert p1 == p2


def test_lt_par_nom():
    a = Produit("A-001", "Alpha", "Cat", 1, 2)
    b = Produit("B-001", "Beta", "Cat", 1, 2)
    assert sorted([b, a])[0] == a


def test_hash_identique_meme_ref():
    p1 = Produit("A-001", "AAA", "Cat", 1, 2)
    p2 = Produit("A-001", "BBB", "Cat", 1, 2)
    assert hash(p1) == hash(p2)


def test_str_contient_ref():
    assert "A-001" in str(Produit("A-001", "AAA", "Cat", 1, 2))


def test_repr_contient_nom():
    assert "AAA" in repr(Produit("A-001", "AAA", "Cat", 1, 2))


def test_qte_negative_interdite():
    p = Produit("A-001", "AAA", "Cat", 1, 2)
    with pytest.raises(ValueError):
        p.qte = -1


def test_qte_type_interdit():
    p = Produit("A-001", "AAA", "Cat", 1, 2)
    with pytest.raises(TypeError):
        p.qte = "abc"


def test_types_mouvement_disponibles():
    types = Mouvement.types_disponibles()
    assert "entree" in types and "sortie" in types and "retour" in types and "inventaire" in types


@pytest.mark.parametrize("type_mvt", ["entree", "sortie", "retour", "inventaire"])
def test_factory_mouvement(type_mvt):
    m = Mouvement.creer(type_mvt, ref_produit="A", qte=1, qte_avant=0, qte_apres=1, note="")
    assert m.TYPE == type_mvt


def test_mouvement_str():
    m = Mouvement.creer("entree", ref_produit="A", qte=1, qte_avant=0, qte_apres=1, note="")
    assert "entree" in str(m)
