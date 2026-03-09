from __future__ import annotations

import pytest

from models.produit import Produit
from services.stock_service import StockService


def test_singleton(stock_vide, tmp_path):
    service2 = StockService(db_path=str(tmp_path / "x.db"), seed_demo=False)
    assert stock_vide is service2


def test_len_contains_iter(stock_peuple):
    assert len(stock_peuple) == 5
    assert "CRAY-001" in stock_peuple
    assert len(list(iter(stock_peuple))) == 5


def test_ajouter_produit(stock_vide):
    p = Produit("TEST-001", "Produit", "Test", 1, 2, 3, 1)
    stock_vide.ajouter_produit(p)
    assert stock_vide.get_produit("TEST-001").nom == "Produit"


def test_ajouter_produit_existant(stock_peuple):
    with pytest.raises(ValueError):
        stock_peuple.ajouter_produit(Produit("CRAY-001", "x", "x", 1, 2))


def test_get_produit_inconnu(stock_peuple):
    with pytest.raises(KeyError):
        stock_peuple.get_produit("NONE-001")


def test_entree_augmente(stock_peuple):
    avant = stock_peuple.get_produit("CRAY-001").qte
    stock_peuple.entree_stock("CRAY-001", 10)
    assert stock_peuple.get_produit("CRAY-001").qte == avant + 10


def test_sortie_diminue(stock_peuple):
    stock_peuple.sortie_stock("CRAY-001", 20)
    assert stock_peuple.get_produit("CRAY-001").qte == 80


def test_sortie_insuffisant(stock_peuple):
    with pytest.raises(ValueError):
        stock_peuple.sortie_stock("GOM-001", 200)


def test_valider_quantite_negative(stock_peuple):
    with pytest.raises(ValueError):
        stock_peuple.entree_stock("CRAY-001", -1)


def test_valider_quantite_zero(stock_peuple):
    with pytest.raises(ValueError):
        stock_peuple.entree_stock("CRAY-001", 0)


def test_valider_quantite_type(stock_peuple):
    with pytest.raises(TypeError):
        stock_peuple.sortie_stock("CRAY-001", "abc")


def test_retour_stock(stock_peuple):
    q = stock_peuple.get_produit("CRAY-001").qte
    stock_peuple.retour_stock("CRAY-001", 2)
    assert stock_peuple.get_produit("CRAY-001").qte == q + 2


def test_inventaire_stock(stock_peuple):
    stock_peuple.inventaire_stock("CRAY-001", 50)
    assert stock_peuple.get_produit("CRAY-001").qte == 50


def test_inventaire_pas_de_changement(stock_peuple):
    stock_peuple.inventaire_stock("CRAY-001", 100)
    assert stock_peuple.get_produit("CRAY-001").qte == 100


def test_historique_genere(stock_peuple):
    stock_peuple.sortie_stock("CRAY-001", 5, "vente")
    hist = stock_peuple.get_historique("CRAY-001")
    assert len(hist) >= 1
    assert hist[0]["type_mvt"] == "sortie"


def test_dernieres_operations_limite(stock_peuple):
    for _ in range(3):
        stock_peuple.entree_stock("CRAY-001", 1)
    assert len(stock_peuple.dernieres_operations(2)) == 2


def test_produits_en_alerte(stock_peuple):
    refs = {p.ref for p in stock_peuple.produits_en_alerte()}
    assert "GOM-001" in refs and "CAR-001" in refs


def test_par_categorie(stock_peuple):
    cat = stock_peuple.par_categorie()
    assert "Écriture" in cat and "Papier" in cat


def test_valeur_totale(stock_peuple):
    assert stock_peuple.valeur_totale_stock() > 0


def test_top_valeur(stock_peuple):
    top = stock_peuple.top_valeur(2)
    assert len(top) == 2
    assert top[0].valeur_stock() >= top[1].valeur_stock()


def test_rechercher(stock_peuple):
    result = stock_peuple.rechercher("cray")
    assert any(p.ref == "CRAY-001" for p in result)


def test_stats_categories(stock_peuple):
    stats = stock_peuple.stats_categories()
    assert stats["Papier"]["nb_produits"] == 2


def test_kpis(stock_peuple):
    k = stock_peuple.kpis()
    assert k["nb_produits"] == 5
    assert "valeur_stock" in k


def test_flux_export(stock_peuple):
    rows = list(stock_peuple.flux_export())
    assert rows[0][0] == "ref"
    assert len(rows) == 6
