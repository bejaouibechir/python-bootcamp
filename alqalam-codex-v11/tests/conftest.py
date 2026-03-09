from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.produit import Produit
from services.stock_service import StockService


@pytest.fixture
def stock_vide(tmp_path):
    db = tmp_path / "test_stock.db"
    StockService.reset_singleton()
    service = StockService(db_path=str(db), seed_demo=False)
    yield service
    StockService.reset_singleton()


@pytest.fixture
def stock_peuple(stock_vide):
    produits = [
        Produit("CRAY-001", "Crayon HB", "Écriture", 0.15, 0.50, 100, 20),
        Produit("STYL-001", "Stylo Bleu", "Écriture", 0.30, 0.90, 5, 30),
        Produit("GOM-001", "Gomme", "Effaçage", 0.20, 0.70, 2, 10),
        Produit("PAP-A4", "Papier A4", "Papier", 2.50, 5.00, 500, 50),
        Produit("CAR-001", "Carnet A5", "Papier", 1.20, 3.50, 0, 10),
    ]
    for p in produits:
        stock_vide.ajouter_produit(p)
    return stock_vide
