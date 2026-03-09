from __future__ import annotations

import pandas as pd

from alq_io.csv_handler import exporter_stock, importer_catalogue
from alq_io.excel_handler import exporter_rapport_complet


def test_cycle_sortie_historique(stock_peuple):
    stock_peuple.sortie_stock("CRAY-001", 10, "vente test")
    hist = stock_peuple.get_historique("CRAY-001")
    assert hist[0]["qte"] == 10


def test_cycle_entree_sortie(stock_peuple):
    stock_peuple.entree_stock("CRAY-001", 20)
    stock_peuple.sortie_stock("CRAY-001", 5)
    assert stock_peuple.get_produit("CRAY-001").qte == 115


def test_cycle_export_import_csv(stock_peuple, tmp_path):
    out = tmp_path / "stock.csv"
    exporter_stock(str(out), stock_peuple)
    rapport = importer_catalogue(str(out), stock_peuple)
    assert rapport.mis_a_jour >= 1


def test_cycle_export_excel(stock_peuple, tmp_path):
    out = tmp_path / "stock.xlsx"
    exporter_rapport_complet(str(out), stock_peuple)
    assert out.exists()


def test_cycle_recherche(stock_peuple):
    assert len(stock_peuple.rechercher("papier")) >= 1


def test_cycle_alertes(stock_peuple):
    stock_peuple.sortie_stock("CRAY-001", 90)
    refs = {p.ref for p in stock_peuple.produits_en_alerte()}
    assert "CRAY-001" in refs


def test_cycle_excel_reader(tmp_path):
    p = tmp_path / "bc.xlsx"
    with pd.ExcelWriter(p) as w:
        pd.DataFrame([{"ref": "A-001", "qte_commandee": 1}]).to_excel(w, sheet_name="produits", index=False)
        pd.DataFrame([{"nom": "F", "contact": "1"}]).to_excel(w, sheet_name="fournisseur", index=False)
    assert p.exists()

