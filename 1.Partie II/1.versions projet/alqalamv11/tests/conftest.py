# [V11 - Tests] Fixtures partagées entre tous les fichiers de test.
#
# CONCEPTS PYTEST :
#   @pytest.fixture          : fonction de setup réutilisable
#   scope="function"         : fixture recréée pour chaque test (défaut)
#   tmp_path                 : dossier temporaire fourni par pytest (supprimé après)
#   monkeypatch              : substitution d'attributs/fonctions pendant le test
#   yield                    : setup avant le yield, teardown après
#   SingletonMeta._reset()   : réinitialise le Singleton entre chaque test

import sys
from pathlib import Path

# Ajouter la racine du projet au sys.path pour tous les tests
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from models.produit import Produit
from metaclasses.singleton import SingletonMeta


@pytest.fixture
def produit_demo() -> Produit:
    """
    Retourne un Produit de démonstration valide.

    Fixture de base réutilisée dans test_produit.py et test_stock_service.py.
    Aucun setup ni teardown — la fixture retourne simplement un objet.
    """
    return Produit(
        ref="CRAY-001",
        nom="Crayon HB",
        categorie="Ecriture",
        prix_achat=0.15,
        prix_vente=0.50,
        qte=100,
        seuil_min=20,
    )


@pytest.fixture
def produit_alerte() -> Produit:
    """Produit volontairement en situation d'alerte (qte <= seuil_min)."""
    return Produit("STYL-002", "Stylo Rouge", "Ecriture", 0.30, 0.90, 3, 10)


@pytest.fixture
def produit_rupture() -> Produit:
    """Produit en rupture totale (qte = 0)."""
    return Produit("PAP-A3", "Rame A3", "Papier", 4.00, 8.00, 0, 10)


@pytest.fixture
def db_vide(tmp_path):
    """
    DatabaseService avec une base SQLite temporaire vide.

    tmp_path : fixture pytest qui crée un dossier temporaire unique par test.
    La base est supprimée automatiquement après chaque test.
    """
    from services.database_service import DatabaseService
    return DatabaseService(tmp_path / "test.db")


@pytest.fixture
def stock_vide(tmp_path, monkeypatch):
    """
    StockService avec base SQLite temporaire et Singleton réinitialisé.

    Problème : StockService est un Singleton — le même objet serait réutilisé
    entre les tests si on ne réinitialise pas le registre.

    Solution :
      1. monkeypatch.setattr remplace DB_PATH par un chemin temporaire
      2. SingletonMeta._reset() efface le registre avant ET après le test
      3. yield retourne le service au test
      4. Le teardown (après yield) remet le registre à zéro

    monkeypatch est automatiquement annulé après le test (pas de risque de fuite).
    """
    # Reset avant le test
    SingletonMeta._reset()

    # Rediriger la DB vers un fichier temporaire
    import config
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test_stock.db")

    # Importer APRÈS le patch pour que StockService lise le bon DB_PATH
    from services import stock_service as sm
    import importlib
    importlib.reload(sm)
    svc = sm.StockService()

    yield svc

    # Teardown — nettoyer le Singleton
    SingletonMeta._reset()
    importlib.reload(sm)
