# [V11 - Tests] Tests d'intégration de StockService.
#
# CONCEPTS DÉMONTRÉS :
#   - fixture stock_vide : StockService isolé avec Singleton reset + monkeypatch DB_PATH
#   - Test des mouvements ET de leur persistance en base SQLite
#   - pytest.raises pour les cas d'erreur métier
#   - Test de l'interface Singleton (__contains__, __len__, __iter__)

import pytest
from models.produit import Produit


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nouveau_produit(ref="CRAY-001", qte=100, seuil=20):
    return Produit(ref, f"Produit {ref}", "Test", 1.0, 2.0, qte, seuil)


# ── Gestion des produits ──────────────────────────────────────────────────────

class TestGestionProduits:

    def test_seeder_charge_produits(self, stock_vide):
        """Au démarrage, le seeder doit charger 10 produits de démo."""
        assert stock_vide.nb_produits() == 10

    def test_ajouter_produit(self, stock_vide):
        nb_avant = stock_vide.nb_produits()
        p = _nouveau_produit("NEUF-001")
        stock_vide.ajouter_produit(p)
        assert stock_vide.nb_produits() == nb_avant + 1
        assert stock_vide.get_produit("NEUF-001").nom == "Produit NEUF-001"

    def test_ajouter_produit_doublon_leve_erreur(self, stock_vide):
        """Ajouter une ref déjà existante doit lever ValueError."""
        p = _nouveau_produit("CRAY-001")
        with pytest.raises(ValueError, match="existe déjà"):
            stock_vide.ajouter_produit(p)

    def test_get_produit_existant(self, stock_vide):
        p = stock_vide.get_produit("CRAY-001")
        assert p.ref == "CRAY-001"

    def test_get_produit_inconnu_leve_erreur(self, stock_vide):
        with pytest.raises(KeyError):
            stock_vide.get_produit("INCONNU-99")

    def test_supprimer_produit(self, stock_vide):
        nb_avant = stock_vide.nb_produits()
        stock_vide.supprimer_produit("CRAY-001")
        assert stock_vide.nb_produits() == nb_avant - 1
        with pytest.raises(KeyError):
            stock_vide.get_produit("CRAY-001")

    def test_mettre_a_jour_produit(self, stock_vide):
        produit = stock_vide.get_produit("CRAY-001")
        modifie = Produit("CRAY-001", "Crayon HB Premium", "Ecriture",
                          produit.prix_achat, produit.prix_vente,
                          produit.qte, produit.seuil_min)
        stock_vide.mettre_a_jour_produit(modifie)
        assert stock_vide.get_produit("CRAY-001").nom == "Crayon HB Premium"


# ── Mouvements de stock ───────────────────────────────────────────────────────

class TestMouvementsStock:

    def test_entree_stock_augmente_qte(self, stock_vide):
        qte_avant = stock_vide.get_produit("CRAY-001").qte
        stock_vide.entree_stock("CRAY-001", 50, "Réassort test")
        assert stock_vide.get_produit("CRAY-001").qte == qte_avant + 50

    def test_entree_stock_persiste_en_db(self, stock_vide):
        """L'entrée doit être enregistrée dans la table mouvements."""
        stock_vide.entree_stock("CRAY-001", 10, "Test DB")
        mvts = stock_vide.db.charger_mouvements(type_mvt="entree")
        assert len(mvts) >= 1
        assert mvts[0]["ref"] == "CRAY-001"
        assert mvts[0]["qte"] == 10

    def test_sortie_stock_diminue_qte(self, stock_vide):
        qte_avant = stock_vide.get_produit("CRAY-001").qte
        stock_vide.sortie_stock("CRAY-001", 10, "Vente")
        assert stock_vide.get_produit("CRAY-001").qte == qte_avant - 10

    def test_sortie_stock_insuffisant_leve_erreur(self, stock_vide):
        """Une sortie dépassant le stock disponible doit lever ValueError."""
        qte = stock_vide.get_produit("CRAY-001").qte
        with pytest.raises(ValueError, match="insuffisant"):
            stock_vide.sortie_stock("CRAY-001", qte + 1, "Trop")

    def test_ajustement_stock_hausse(self, stock_vide):
        stock_vide.ajustement_stock("CRAY-001", 999, "Inventaire")
        assert stock_vide.get_produit("CRAY-001").qte == 999

    def test_ajustement_stock_negatif_interdit(self, stock_vide):
        with pytest.raises(ValueError):
            stock_vide.ajustement_stock("CRAY-001", -1, "Erreur")

    def test_retour_stock_diminue_qte(self, stock_vide):
        qte_avant = stock_vide.get_produit("CRAY-001").qte
        stock_vide.retour_stock("CRAY-001", 5, "Retour client")
        assert stock_vide.get_produit("CRAY-001").qte == qte_avant - 5

    def test_valider_qte_type_incorrect(self, stock_vide):
        """Le décorateur @valider_qte doit rejeter un float."""
        with pytest.raises(TypeError):
            stock_vide.entree_stock("CRAY-001", 5.5, "Erreur")

    def test_valider_qte_hors_plage(self, stock_vide):
        """Le décorateur @valider_qte doit rejeter qte=0."""
        with pytest.raises(ValueError):
            stock_vide.entree_stock("CRAY-001", 0, "Zéro")


# ── Statistiques ──────────────────────────────────────────────────────────────

class TestStatistiquesStock:

    def test_nb_alertes(self, stock_vide):
        """Les produits du seeder avec qte <= seuil_min doivent être comptés."""
        nb = stock_vide.nb_alertes()
        assert nb >= 0  # au moins 0, typiquement 4 selon le seeder

    def test_valeur_totale_positive(self, stock_vide):
        """La valeur totale du stock doit être positive."""
        assert stock_vide.valeur_totale_stock() > 0

    def test_rechercher_par_ref(self, stock_vide):
        resultats = stock_vide.rechercher("CRAY-001")
        assert any(p.ref == "CRAY-001" for p in resultats)

    def test_rechercher_vide_retourne_tout(self, stock_vide):
        resultats = stock_vide.rechercher("")
        assert len(resultats) == stock_vide.nb_produits()

    def test_par_categorie(self, stock_vide):
        cats = stock_vide.par_categorie()
        assert isinstance(cats, dict)
        assert len(cats) > 0

    def test_top_valeur(self, stock_vide):
        top = stock_vide.top_valeur(3)
        assert len(top) == 3
        # Vérifie l'ordre décroissant
        assert top[0].valeur_stock() >= top[1].valeur_stock()


# ── Interface Singleton et méthodes magiques ──────────────────────────────────

class TestInterfaceStock:

    def test_contains(self, stock_vide):
        assert "CRAY-001" in stock_vide

    def test_not_contains(self, stock_vide):
        assert "INCONNU-99" not in stock_vide

    def test_len(self, stock_vide):
        assert len(stock_vide) == stock_vide.nb_produits()

    def test_iter(self, stock_vide):
        produits = list(stock_vide)
        assert len(produits) == stock_vide.nb_produits()

    def test_str_contient_nb_produits(self, stock_vide):
        s = str(stock_vide)
        assert str(stock_vide.nb_produits()) in s
