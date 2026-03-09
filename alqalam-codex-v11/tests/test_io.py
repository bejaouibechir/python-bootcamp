from __future__ import annotations

import pandas as pd
import pytest

from alq_io.csv_handler import exporter_stock, importer_catalogue
from alq_io.excel_handler import exporter_rapport_complet, importer_bon_commande
from alq_io.validator import (
    normaliser_prix,
    normaliser_ref,
    rechercher_dans_logs,
    valider_prix,
    valider_qte,
    valider_ref,
)


def test_valider_ref_ok():
    assert valider_ref("CRAY-001").valide


def test_valider_ref_ko():
    assert not valider_ref("cray001").valide


def test_valider_prix_ok():
    assert valider_prix("1,50").valide


def test_valider_prix_ko():
    assert not valider_prix("1,500").valide


def test_valider_qte():
    assert valider_qte("123").valide


def test_normaliser_prix():
    assert normaliser_prix("1,50") == 1.5


def test_normaliser_ref():
    assert normaliser_ref("cray001") == "CRAY-001"


def test_rechercher_logs_ok():
    lignes = ["2026-01-01 10:00:00,123 | INFO | sortie CRAY-001", "x"]
    assert len(rechercher_dans_logs("sortie", lignes)) == 1


def test_rechercher_logs_regex_ko():
    with pytest.raises(ValueError):
        rechercher_dans_logs("[", ["x"])


def test_import_csv_valide(stock_vide, tmp_path):
    csv_path = tmp_path / "catalogue.csv"
    csv_path.write_text(
        "ref,nom,categorie,prix_achat,prix_vente,qte,seuil_min\n"
        "TEST-001,Produit Test,Test,1.00,2.00,50,5\n",
        encoding="utf-8",
    )
    rapport = importer_catalogue(str(csv_path), stock_vide)
    assert rapport.importes == 1
    assert "TEST-001" in stock_vide


def test_import_csv_colonnes_manquantes(stock_vide, tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("ref,nom\nTEST-001,Produit\n", encoding="utf-8")
    with pytest.raises(ValueError):
        importer_catalogue(str(csv_path), stock_vide)


def test_import_csv_ligne_rejetee(stock_vide, tmp_path):
    csv_path = tmp_path / "badline.csv"
    csv_path.write_text(
        "ref,nom,categorie,prix_achat,prix_vente,qte,seuil_min\n"
        "inv,Produit Test,Test,1.00,2.00,50,5\n",
        encoding="utf-8",
    )
    rapport = importer_catalogue(str(csv_path), stock_vide)
    assert rapport.rejetes == 1


def test_export_csv(stock_peuple, tmp_path):
    out = tmp_path / "out.csv"
    nb = exporter_stock(str(out), stock_peuple)
    assert nb == 5
    assert out.exists()


def test_export_excel(stock_peuple, tmp_path):
    out = tmp_path / "rapport.xlsx"
    exporter_rapport_complet(str(out), stock_peuple)
    assert out.exists()


def test_import_bon_commande(stock_vide, tmp_path):
    path = tmp_path / "bc.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([{"ref": "TEST-001", "qte_commandee": 10}]).to_excel(writer, sheet_name="produits", index=False)
        pd.DataFrame([{"nom": "Fournisseur A", "contact": "x"}]).to_excel(writer, sheet_name="fournisseur", index=False)
    data = importer_bon_commande(str(path))
    assert "fournisseur" in data and len(data["lignes"]) == 1


def test_import_bon_commande_feuilles_manquantes(tmp_path):
    path = tmp_path / "bc_bad.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([{"a": 1}]).to_excel(writer, sheet_name="x", index=False)
    with pytest.raises(ValueError):
        importer_bon_commande(str(path))

