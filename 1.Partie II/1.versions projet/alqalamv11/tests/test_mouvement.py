# [V11 - Tests] Tests unitaires du modèle Mouvement et de sa factory.
#
# CONCEPTS DÉMONTRÉS :
#   - Test de la factory (Mouvement.fabriquer)
#   - pytest.raises avec match= pour vérifier le message d'erreur
#   - Test des méthodes de classification (est_entree, est_sortie, est_ajustement)

import pytest
from models.mouvement import Mouvement
import models.types_mouvement  # force l'enregistrement des 4 sous-classes


# ── Création directe ──────────────────────────────────────────────────────────

class TestCreationMouvement:
    """Tests de création d'un Mouvement de base."""

    def test_creation_entree_valide(self):
        m = Mouvement("CRAY-001", "entree", 50, "Réassort")
        assert m.ref_produit == "CRAY-001"
        assert m.type_mvt    == "entree"
        assert m.qte         == 50
        assert m.note        == "Réassort"

    def test_creation_sortie_valide(self):
        m = Mouvement("STYL-001", "sortie", 10)
        assert m.type_mvt == "sortie"
        assert m.qte      == 10

    def test_type_invalide_leve_erreur(self):
        """Un type inconnu doit lever ValueError."""
        with pytest.raises(ValueError, match="Type de mouvement invalide"):
            Mouvement("CRAY-001", "inconnu", 5)

    def test_qte_zero_interdit(self):
        """Une quantité nulle doit lever ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Mouvement("CRAY-001", "entree", 0)

    def test_qte_negative_interdite(self):
        """Une quantité négative doit lever ValueError."""
        with pytest.raises(ValueError):
            Mouvement("CRAY-001", "entree", -10)

    def test_date_est_renseignee(self):
        """Le champ date doit être automatiquement renseigné à la création."""
        m = Mouvement("CRAY-001", "entree", 1)
        assert m.date is not None
        assert len(m.date) > 10  # format ISO — au moins YYYY-MM-DD


# ── Factory fabriquer() ───────────────────────────────────────────────────────

class TestFactoryMouvement:
    """Tests de Mouvement.fabriquer() — le registre de métaclasses."""

    @pytest.mark.parametrize("type_mvt, classe_attendue", [
        ("entree",      "EntreeMouvement"),
        ("sortie",      "SortieMouvement"),
        ("ajustement",  "AjustementMouvement"),
        ("retour",      "RetourMouvement"),
    ])
    def test_fabriquer_retourne_bonne_classe(self, type_mvt, classe_attendue):
        """fabriquer() doit retourner une instance de la sous-classe enregistrée."""
        mvt = Mouvement.fabriquer(type_mvt, "CRAY-001", 5)
        assert type(mvt).__name__ == classe_attendue

    def test_fabriquer_entree_incremente_pas_stock(self):
        """fabriquer() crée l'objet — il ne modifie pas le stock."""
        mvt = Mouvement.fabriquer("entree", "CRAY-001", 50, "Bon de commande")
        assert mvt.ref_produit == "CRAY-001"
        assert mvt.qte         == 50
        assert mvt.note        == "Bon de commande"

    def test_fabriquer_type_mvt_correct(self):
        """Le type_mvt de l'objet fabriqué doit correspondre au type demandé."""
        for t in ("entree", "sortie", "ajustement", "retour"):
            mvt = Mouvement.fabriquer(t, "TEST-01", 1)
            assert mvt.type_mvt == t


# ── Classification ────────────────────────────────────────────────────────────

class TestClassificationMouvement:
    """Tests des méthodes de classification."""

    def test_est_entree_true(self):
        m = Mouvement.fabriquer("entree", "CRAY-001", 10)
        assert m.est_entree() is True
        assert m.est_sortie() is False

    def test_est_sortie_true(self):
        m = Mouvement.fabriquer("sortie", "CRAY-001", 5)
        assert m.est_sortie() is True
        assert m.est_entree() is False

    def test_retour_est_entree(self):
        """Un retour fournisseur compte comme une entrée (stock remis en rayon)."""
        m = Mouvement.fabriquer("retour", "CRAY-001", 2)
        assert m.est_entree() is True

    def test_est_ajustement(self):
        m = Mouvement.fabriquer("ajustement", "CRAY-001", 1)
        assert m.est_ajustement() is True

    def test_str_contient_ref(self):
        """__str__ doit mentionner la référence produit."""
        m = Mouvement.fabriquer("entree", "CRAY-001", 10)
        assert "CRAY-001" in str(m)


# ── Sérialisation ─────────────────────────────────────────────────────────────

class TestSerialisationMouvement:

    def test_to_dict_cles(self):
        m = Mouvement("CRAY-001", "entree", 10)
        d = m.to_dict()
        assert set(d.keys()) == {"ref_produit", "type_mvt", "qte", "note", "date"}

    def test_to_dict_valeurs(self):
        m = Mouvement("CRAY-001", "sortie", 5, "Vente")
        d = m.to_dict()
        assert d["ref_produit"] == "CRAY-001"
        assert d["type_mvt"]    == "sortie"
        assert d["qte"]         == 5
        assert d["note"]        == "Vente"
