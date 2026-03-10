# [V11 - Tests] Tests unitaires de CsvService.
#
# CONCEPTS DÉMONTRÉS :
#   - fixture stock_vide  : StockService isolé avec Singleton reset
#   - tmp_path            : dossier temporaire pour créer des fichiers CSV de test
#   - Test d'un import CSV complet (nouveau produit + mise à jour + ligne invalide)
#   - Test des 3 exports (catalogue, mouvements, comptabilité)
#   - pytest.raises pour les erreurs de structure CSV

import pytest
import csv
from pathlib import Path
from services.csv_service import CsvService, ErreurCsv


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ecrire_csv(chemin: Path, entetes: list, lignes: list[list]) -> None:
    """Utilitaire : écrit un fichier CSV de test."""
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(entetes)
        writer.writerows(lignes)


ENTETES_CATALOGUE = ["ref", "nom", "categorie", "prix_achat", "prix_vente", "seuil_min"]


# ── Import catalogue ──────────────────────────────────────────────────────────

class TestImportCatalogue:

    def test_import_nouveau_produit(self, stock_vide, tmp_path):
        """Un produit absent du stock doit être ajouté avec qte=0."""
        fichier = tmp_path / "catalogue.csv"
        _ecrire_csv(fichier, ENTETES_CATALOGUE, [
            ["NEUF-001", "Produit Neuf", "Test", "1.50", "3.00", "10"],
        ])
        svc     = CsvService(stock_vide)
        rapport = svc.importer_catalogue(fichier)

        assert rapport["importes"]   == 1
        assert rapport["mis_a_jour"] == 0
        assert rapport["erreurs"]    == []
        p = stock_vide.get_produit("NEUF-001")
        assert p.nom      == "Produit Neuf"
        assert p.qte      == 0          # qte initiale = 0 à l'import
        assert p.seuil_min == 10

    def test_import_mise_a_jour_produit_existant(self, stock_vide, tmp_path):
        """Un produit déjà présent dans le stock doit être mis à jour."""
        fichier = tmp_path / "update.csv"
        # CRAY-001 existe dans le seeder — on change son nom et son prix
        _ecrire_csv(fichier, ENTETES_CATALOGUE, [
            ["CRAY-001", "Crayon HB Premium", "Ecriture", "0.20", "0.70", "25"],
        ])
        svc     = CsvService(stock_vide)
        rapport = svc.importer_catalogue(fichier)

        assert rapport["mis_a_jour"] == 1
        assert rapport["importes"]   == 0
        p = stock_vide.get_produit("CRAY-001")
        assert p.nom       == "Crayon HB Premium"
        assert p.prix_achat == 0.20
        assert p.seuil_min  == 25

    def test_import_ligne_invalide_continue(self, stock_vide, tmp_path):
        """Une ligne invalide doit être ignorée sans stopper l'import."""
        fichier = tmp_path / "mixte.csv"
        _ecrire_csv(fichier, ENTETES_CATALOGUE, [
            ["NEUF-002", "Bon produit", "Test", "1.00", "2.00", "5"],
            ["",         "Sans ref",   "Test", "1.00", "2.00", "5"],   # ref vide → erreur
            ["NEUF-003", "Autre bon",  "Test", "0.50", "1.00", "3"],
        ])
        svc     = CsvService(stock_vide)
        rapport = svc.importer_catalogue(fichier)

        assert rapport["importes"]    == 2
        assert len(rapport["erreurs"]) == 1
        assert rapport["total_lues"]   == 3

    def test_import_colonnes_manquantes_leve_erreur(self, stock_vide, tmp_path):
        """Un CSV sans les colonnes requises doit lever ErreurCsv."""
        fichier = tmp_path / "mauvais.csv"
        _ecrire_csv(fichier, ["ref", "nom"], [["CRAY-001", "Crayon"]])
        svc = CsvService(stock_vide)
        with pytest.raises(ErreurCsv, match="Colonnes manquantes"):
            svc.importer_catalogue(fichier)

    def test_import_fichier_inexistant_leve_erreur(self, stock_vide, tmp_path):
        """Importer un fichier qui n'existe pas doit lever FileNotFoundError."""
        svc = CsvService(stock_vide)
        with pytest.raises(FileNotFoundError):
            svc.importer_catalogue(tmp_path / "inexistant.csv")

    def test_import_plusieurs_produits(self, stock_vide, tmp_path):
        """Un catalogue avec 3 nouveaux produits doit tous les importer."""
        fichier = tmp_path / "multi.csv"
        _ecrire_csv(fichier, ENTETES_CATALOGUE, [
            ["AAAA-001", "Prod A", "Cat1", "1.0", "2.0", "5"],
            ["BBBB-001", "Prod B", "Cat2", "2.0", "4.0", "3"],
            ["CCCC-001", "Prod C", "Cat1", "0.5", "1.0", "10"],
        ])
        svc     = CsvService(stock_vide)
        rapport = svc.importer_catalogue(fichier)
        assert rapport["importes"] == 3


# ── Exports ───────────────────────────────────────────────────────────────────

class TestExportsCsv:

    def test_export_catalogue_cree_fichier(self, stock_vide, tmp_path):
        """exporter_catalogue() doit créer un fichier CSV lisible."""
        fichier = tmp_path / "cat_export.csv"
        svc     = CsvService(stock_vide)
        nb      = svc.exporter_catalogue(fichier)

        assert fichier.exists()
        assert nb == stock_vide.nb_produits()

    def test_export_catalogue_contient_tous_produits(self, stock_vide, tmp_path):
        """Le CSV exporté doit contenir autant de lignes que de produits (+ en-tête)."""
        fichier = tmp_path / "cat.csv"
        svc     = CsvService(stock_vide)
        svc.exporter_catalogue(fichier)

        with open(fichier, encoding="utf-8-sig") as f:
            lignes = list(csv.DictReader(f))
        assert len(lignes) == stock_vide.nb_produits()

    def test_export_catalogue_entetes_correctes(self, stock_vide, tmp_path):
        """Le CSV doit avoir les bonnes colonnes."""
        fichier = tmp_path / "entetes.csv"
        svc     = CsvService(stock_vide)
        svc.exporter_catalogue(fichier)

        with open(fichier, encoding="utf-8-sig") as f:
            entetes = csv.DictReader(f).fieldnames
        assert "ref"        in entetes
        assert "nom"        in entetes
        assert "prix_achat" in entetes
        assert "qte"        in entetes

    def test_export_mouvements_apres_operation(self, stock_vide, tmp_path):
        """Après une entrée stock, l'export mouvements doit contenir au moins 1 ligne."""
        stock_vide.entree_stock("CRAY-001", 10, "Test export")
        fichier = tmp_path / "mvts.csv"
        svc     = CsvService(stock_vide)
        nb      = svc.exporter_mouvements(fichier)

        assert fichier.exists()
        assert nb >= 1

    def test_export_comptabilite_calcule_valeurs(self, stock_vide, tmp_path):
        """L'export comptabilité doit calculer valeur_stock et marge."""
        fichier = tmp_path / "compta.csv"
        svc     = CsvService(stock_vide)
        svc.exporter_comptabilite(fichier)

        with open(fichier, encoding="utf-8-sig") as f:
            lignes = list(csv.DictReader(f))
        assert len(lignes) == stock_vide.nb_produits()
        # Vérifier que valeur_stock et marge sont présentes
        assert "valeur_stock"    in lignes[0]
        assert "marge_unitaire"  in lignes[0]
