# [V11 - Tests] Tests unitaires de DatabaseService.
#
# CONCEPTS DÉMONTRÉS :
#   - fixture db_vide (tmp_path) : base SQLite temporaire → isolation totale
#   - Test CRUD complet : inserer, charger, mettre_a_jour, supprimer
#   - Test des filtres dynamiques de charger_mouvements()
#   - Test de migration JSON → SQLite
#   - sqlite3.IntegrityError pour les violations de contrainte

import pytest
import json
import sqlite3
from pathlib import Path
from services.database_service import DatabaseService


# ── Données de test ───────────────────────────────────────────────────────────

PRODUIT_A = {
    "ref": "CRAY-001", "nom": "Crayon HB", "categorie": "Ecriture",
    "prix_achat": 0.15, "prix_vente": 0.50, "qte": 100, "seuil_min": 20,
}
PRODUIT_B = {
    "ref": "STYL-001", "nom": "Stylo Bleu", "categorie": "Ecriture",
    "prix_achat": 0.30, "prix_vente": 0.90, "qte": 50, "seuil_min": 10,
}
MOUVEMENT_ENTREE = {
    "date": "2026-03-10T10:00:00", "type_mvt": "entree",
    "ref": "CRAY-001", "produit": "Crayon HB", "qte": 20, "note": "Réassort",
}
MOUVEMENT_SORTIE = {
    "date": "2026-03-10T11:00:00", "type_mvt": "sortie",
    "ref": "CRAY-001", "produit": "Crayon HB", "qte": 5, "note": "Vente",
}


# ── Schéma ────────────────────────────────────────────────────────────────────

class TestSchema:
    def test_tables_creees(self, db_vide):
        """Les tables produits et mouvements doivent exister après init."""
        import sqlite3 as sq
        conn = sq.connect(str(db_vide._chemin))
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        conn.close()
        assert "produits"   in tables
        assert "mouvements" in tables

    def test_index_crees(self, db_vide):
        """Les index de performance doivent être créés."""
        import sqlite3 as sq
        conn = sq.connect(str(db_vide._chemin))
        index = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()}
        conn.close()
        assert "idx_mvt_date" in index
        assert "idx_mvt_ref"  in index
        assert "idx_mvt_type" in index


# ── CRUD Produits ─────────────────────────────────────────────────────────────

class TestCrudProduits:

    def test_base_vide_retourne_liste_vide(self, db_vide):
        assert db_vide.charger_produits() == []

    def test_inserer_et_charger_produit(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        produits = db_vide.charger_produits()
        assert len(produits) == 1
        assert produits[0]["ref"] == "CRAY-001"
        assert produits[0]["nom"] == "Crayon HB"

    def test_inserer_doublon_leve_erreur(self, db_vide):
        """Insérer deux fois la même ref doit lever IntegrityError."""
        db_vide.inserer_produit(PRODUIT_A)
        with pytest.raises(sqlite3.IntegrityError):
            db_vide.inserer_produit(PRODUIT_A)

    def test_mettre_a_jour_produit(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        modifie = {**PRODUIT_A, "nom": "Crayon HB Modifie", "qte": 200}
        db_vide.mettre_a_jour_produit(modifie)
        produits = db_vide.charger_produits()
        assert produits[0]["nom"] == "Crayon HB Modifie"
        assert produits[0]["qte"] == 200

    def test_mettre_a_jour_qte_seulement(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.mettre_a_jour_qte("CRAY-001", 999)
        produits = db_vide.charger_produits()
        assert produits[0]["qte"]       == 999
        assert produits[0]["nom"]       == "Crayon HB"  # inchangé

    def test_supprimer_produit(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.supprimer_produit("CRAY-001")
        assert db_vide.charger_produits() == []

    def test_ref_existe_true(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        assert db_vide.ref_existe("CRAY-001") is True

    def test_ref_existe_false(self, db_vide):
        assert db_vide.ref_existe("INCONNU-99") is False

    def test_charger_plusieurs_produits_tries(self, db_vide):
        """Les produits doivent être retournés triés par ref."""
        db_vide.inserer_produit(PRODUIT_B)
        db_vide.inserer_produit(PRODUIT_A)
        produits = db_vide.charger_produits()
        refs = [p["ref"] for p in produits]
        assert refs == sorted(refs)


# ── CRUD Mouvements ───────────────────────────────────────────────────────────

class TestCrudMouvements:

    def test_inserer_et_charger_mouvement(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)
        mvts = db_vide.charger_mouvements()
        assert len(mvts) == 1
        assert mvts[0]["type_mvt"] == "entree"
        assert mvts[0]["qte"]      == 20

    def test_nb_mouvements_vide(self, db_vide):
        assert db_vide.nb_mouvements() == 0

    def test_nb_mouvements_apres_insertions(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)
        db_vide.inserer_mouvement(MOUVEMENT_SORTIE)
        assert db_vide.nb_mouvements() == 2

    def test_charger_sans_filtre_ordre_desc(self, db_vide):
        """Sans filtre, les mouvements doivent être triés du plus récent au plus ancien."""
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)
        db_vide.inserer_mouvement(MOUVEMENT_SORTIE)
        mvts = db_vide.charger_mouvements()
        # Le plus récent (11h) doit être en premier
        assert mvts[0]["date"] > mvts[1]["date"]

    def test_filtre_type_mvt(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)
        db_vide.inserer_mouvement(MOUVEMENT_SORTIE)
        entrees = db_vide.charger_mouvements(type_mvt="entree")
        assert len(entrees) == 1
        assert entrees[0]["type_mvt"] == "entree"

    def test_filtre_ref(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_produit(PRODUIT_B)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)
        mvt_b = {**MOUVEMENT_SORTIE, "ref": "STYL-001", "produit": "Stylo Bleu"}
        db_vide.inserer_mouvement(mvt_b)
        filtres = db_vide.charger_mouvements(ref="CRAY-001")
        assert len(filtres) == 1
        assert filtres[0]["ref"] == "CRAY-001"

    def test_filtre_limite(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        for i in range(10):
            db_vide.inserer_mouvement({**MOUVEMENT_ENTREE, "date": f"2026-03-10T{i:02d}:00:00"})
        assert len(db_vide.charger_mouvements(limite=3)) == 3

    def test_refs_distinctes(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_produit(PRODUIT_B)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)
        db_vide.inserer_mouvement({**MOUVEMENT_SORTIE, "ref": "STYL-001", "produit": "Stylo"})
        refs = db_vide.refs_distinctes()
        assert "CRAY-001" in refs
        assert "STYL-001" in refs


# ── Agrégation ────────────────────────────────────────────────────────────────

class TestStats:

    def test_stats_mouvements_vide(self, db_vide):
        """Sur une base vide, toutes les stats doivent être à zéro."""
        stats = db_vide.stats_mouvements()
        for t in ("entree", "sortie", "ajustement", "retour"):
            assert stats[t]["nb"]         == 0
            assert stats[t]["qte_totale"] == 0

    def test_stats_mouvements_apres_insertions(self, db_vide):
        db_vide.inserer_produit(PRODUIT_A)
        db_vide.inserer_mouvement(MOUVEMENT_ENTREE)  # qte=20
        db_vide.inserer_mouvement({**MOUVEMENT_ENTREE, "qte": 30})  # qte=30
        db_vide.inserer_mouvement(MOUVEMENT_SORTIE)   # qte=5
        stats = db_vide.stats_mouvements()
        assert stats["entree"]["nb"]         == 2
        assert stats["entree"]["qte_totale"] == 50
        assert stats["sortie"]["nb"]         == 1
        assert stats["sortie"]["qte_totale"] == 5


# ── Migration JSON ────────────────────────────────────────────────────────────

class TestMigration:

    def test_migration_depuis_json(self, tmp_path):
        """La migration doit importer les produits du JSON dans SQLite."""
        # Préparer un stock.json fictif
        json_path = tmp_path / "stock.json"
        data = [PRODUIT_A, PRODUIT_B]
        json_path.write_text(json.dumps(data), encoding="utf-8")

        db = DatabaseService(tmp_path / "migration.db")
        nb = db.migrer_depuis_json(json_path)

        assert nb == 2
        produits = db.charger_produits()
        assert len(produits) == 2
        # Le JSON doit être renommé en .bak
        assert not json_path.exists()
        assert (tmp_path / "stock.json.bak").exists()

    def test_migration_ignoree_si_json_absent(self, tmp_path):
        """Si aucun JSON n'existe, migrer_depuis_json() doit retourner 0."""
        db = DatabaseService(tmp_path / "vide.db")
        nb = db.migrer_depuis_json(tmp_path / "inexistant.json")
        assert nb == 0

    def test_migration_ignoree_si_db_non_vide(self, tmp_path):
        """Si la table contient déjà des données, la migration ne doit pas s'exécuter."""
        json_path = tmp_path / "stock.json"
        json_path.write_text(json.dumps([PRODUIT_A]), encoding="utf-8")

        db = DatabaseService(tmp_path / "existant.db")
        db.inserer_produit(PRODUIT_A)  # base déjà peuplée

        nb = db.migrer_depuis_json(json_path)
        assert nb == 0
        assert json_path.exists()  # le JSON n'a pas été renommé
