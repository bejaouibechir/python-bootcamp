# [V11 - Tests] Tests unitaires du modèle Produit.
#
# CONCEPTS DÉMONTRÉS :
#   - Test nominal : vérifier le comportement attendu
#   - pytest.raises : vérifier que les erreurs sont bien levées
#   - @pytest.mark.parametrize : même test avec plusieurs jeux de données
#   - Fixture conftest : produit_demo réutilisé sans répétition

import pytest
from models.produit import Produit


# ── Création ──────────────────────────────────────────────────────────────────

class TestCreationProduit:
    """Tests de création et validation des attributs."""

    def test_creation_valide(self, produit_demo):
        """Un Produit créé avec des données valides doit avoir les bons attributs."""
        p = produit_demo
        assert p.ref       == "CRAY-001"
        assert p.nom       == "Crayon HB"
        assert p.categorie == "Ecriture"
        assert p.prix_achat == 0.15
        assert p.prix_vente == 0.50
        assert p.qte        == 100
        assert p.seuil_min  == 20

    def test_ref_vide_interdit(self):
        """Le descripteur NonVide doit rejeter une référence vide."""
        with pytest.raises(ValueError):
            Produit("", "Crayon", "Ecriture", 0.15, 0.50, 10, 5)

    def test_nom_vide_interdit(self):
        """Le descripteur NonVide doit rejeter un nom vide."""
        with pytest.raises(ValueError):
            Produit("CRAY-001", "", "Ecriture", 0.15, 0.50, 10, 5)

    def test_prix_achat_negatif_interdit(self):
        """Le descripteur Positif doit rejeter un prix d'achat négatif."""
        with pytest.raises(ValueError):
            Produit("CRAY-001", "Crayon", "Ecriture", -1.0, 0.50, 10, 5)

    def test_prix_vente_negatif_interdit(self):
        """Le descripteur Positif doit rejeter un prix de vente négatif."""
        with pytest.raises(ValueError):
            Produit("CRAY-001", "Crayon", "Ecriture", 0.15, -0.50, 10, 5)

    def test_qte_negative_interdite(self):
        """Le descripteur PositifEntier doit rejeter une quantité négative."""
        with pytest.raises(ValueError):
            Produit("CRAY-001", "Crayon", "Ecriture", 0.15, 0.50, -5, 5)

    def test_seuil_negatif_interdit(self):
        """Le descripteur PositifEntier doit rejeter un seuil négatif."""
        with pytest.raises(ValueError):
            Produit("CRAY-001", "Crayon", "Ecriture", 0.15, 0.50, 10, -1)

    def test_qte_zero_autorisee(self):
        """Une quantité de 0 (rupture totale) doit être autorisée."""
        p = Produit("CRAY-001", "Crayon", "Ecriture", 0.15, 0.50, 0, 5)
        assert p.qte == 0


# ── Méthodes métier ───────────────────────────────────────────────────────────

class TestMetierProduit:
    """Tests des calculs métier."""

    def test_valeur_stock(self, produit_demo):
        """valeur_stock() = qte * prix_achat."""
        assert produit_demo.valeur_stock() == pytest.approx(100 * 0.15)

    def test_marge_unitaire(self, produit_demo):
        """marge_unitaire() = prix_vente - prix_achat."""
        assert produit_demo.marge_unitaire() == pytest.approx(0.50 - 0.15)

    @pytest.mark.parametrize("qte, seuil, attendu", [
        (0,  10, True),   # rupture totale → alerte
        (5,  10, True),   # stock <= seuil → alerte
        (10, 10, True),   # stock = seuil  → alerte
        (11, 10, False),  # stock > seuil  → OK
        (50, 10, False),  # stock largement OK
    ])
    def test_est_en_alerte(self, qte, seuil, attendu):
        """est_en_alerte() retourne True si qte <= seuil_min."""
        p = Produit("TEST-001", "Produit Test", "Test", 1.0, 2.0, qte, seuil)
        assert p.est_en_alerte() == attendu

    def test_valeur_stock_zero(self, produit_rupture):
        """Un produit en rupture a une valeur de stock nulle."""
        assert produit_rupture.valeur_stock() == 0.0


# ── Sérialisation ─────────────────────────────────────────────────────────────

class TestSerialisationProduit:
    """Tests to_dict() / from_dict()."""

    def test_to_dict_cles(self, produit_demo):
        """to_dict() doit contenir exactement les 7 clés attendues."""
        d = produit_demo.to_dict()
        assert set(d.keys()) == {"ref", "nom", "categorie", "prix_achat", "prix_vente", "qte", "seuil_min"}

    def test_to_dict_valeurs(self, produit_demo):
        """to_dict() doit retourner les bonnes valeurs."""
        d = produit_demo.to_dict()
        assert d["ref"]       == "CRAY-001"
        assert d["qte"]       == 100
        assert d["prix_achat"] == 0.15

    def test_from_dict_reconstruit_produit(self, produit_demo):
        """from_dict(to_dict(p)) doit redonner un produit équivalent."""
        d = produit_demo.to_dict()
        p2 = Produit.from_dict(d)
        assert p2 == produit_demo
        assert p2.qte == produit_demo.qte


# ── Méthodes magiques ─────────────────────────────────────────────────────────

class TestMagiqueProduit:
    """Tests __eq__, __lt__, __hash__, __str__."""

    def test_eq_meme_ref(self):
        """Deux produits avec la même ref sont égaux."""
        p1 = Produit("CRAY-001", "Crayon A", "Ecriture", 0.10, 0.40, 10, 5)
        p2 = Produit("CRAY-001", "Crayon B", "Ecriture", 0.20, 0.60, 20, 5)
        assert p1 == p2

    def test_eq_ref_differentes(self):
        """Deux produits avec des refs différentes sont inégaux."""
        p1 = Produit("CRAY-001", "Crayon", "Ecriture", 0.15, 0.50, 10, 5)
        p2 = Produit("CRAY-002", "Crayon", "Ecriture", 0.15, 0.50, 10, 5)
        assert p1 != p2

    def test_lt_ordre_alphabetique(self):
        """__lt__ compare les noms en minuscules."""
        p1 = Produit("AAAA-01", "Agrafeuse", "Bureau", 5.0, 10.0, 10, 5)
        p2 = Produit("BBBB-01", "Stylo",     "Ecriture", 0.5, 1.0, 10, 5)
        assert p1 < p2

    def test_str_contient_ref(self, produit_demo):
        """__str__ doit contenir la référence du produit."""
        assert "CRAY-001" in str(produit_demo)

    def test_hash_identique_meme_ref(self):
        """Deux produits avec la même ref ont le même hash."""
        p1 = Produit("CRAY-001", "A", "E", 1.0, 2.0, 10, 5)
        p2 = Produit("CRAY-001", "B", "E", 1.0, 2.0, 20, 5)
        assert hash(p1) == hash(p2)
