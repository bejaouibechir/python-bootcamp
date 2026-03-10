# [V11 - Tests] Tests des validateurs regex (validators/regex_validators.py).
#
# CONCEPTS DÉMONTRÉS :
#   - @pytest.mark.parametrize : même logique testée avec N jeux de données
#   - Tuple (entrée, résultat_attendu) dans les parametrize
#   - Test de fonctions pures (pas de side effects, facile à tester)

import pytest
from validators.regex_validators import (
    valider_ref, valider_nom, valider_prix, valider_qte, valider_note,
)


# ── Référence produit ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("ref, valide", [
    ("CRAY-001",  True),   # format standard
    ("PAP-A4",    True),   # alphanum après tiret
    ("STYL-002",  True),   # 4 lettres
    ("AB-1",      True),   # minimum valide
    ("ABCDEF-Z9", True),   # maximum valide
    ("",          False),  # vide
    ("cray-001",  True),   # minuscules → normalisé en majuscules par .upper()
    ("C-001",     False),  # 1 lettre (minimum 2)
    ("CRAY001",   False),  # pas de tiret
    ("CRAY-",     False),  # rien après le tiret
    ("CRAY-123456", False),# trop long après tiret
])
def test_valider_ref(ref, valide):
    ok, _ = valider_ref(ref)
    assert ok == valide


# ── Nom produit ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nom, valide", [
    ("Crayon HB",    True),
    ("AB",           True),   # minimum 2 caractères
    ("A" * 60,       True),   # maximum 60 caractères
    ("",             False),  # vide
    ("A",            False),  # trop court (1 char)
    ("A" * 61,       False),  # trop long
])
def test_valider_nom(nom, valide):
    ok, _ = valider_nom(nom)
    assert ok == valide


# ── Prix ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("prix, valide", [
    ("0",      True),   # zéro
    ("5",      True),   # entier
    ("1.5",    True),   # décimal point
    ("12,90",  True),   # décimal virgule
    ("0.300",  True),   # 3 décimales
    ("",       False),  # vide
    ("-1",     False),  # négatif
    ("1.2345", False),  # trop de décimales
    ("abc",    False),  # non numérique
])
def test_valider_prix(prix, valide):
    ok, _ = valider_prix(prix)
    assert ok == valide


# ── Quantité ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("qte, obligatoire, valide", [
    ("0",   True,  True),
    ("100", True,  True),
    ("",    False, True),   # optionnel → vide OK
    ("",    True,  False),  # obligatoire → vide KO
    ("-1",  True,  False),
    ("1.5", True,  False),  # float non accepté
    ("abc", True,  False),
])
def test_valider_qte(qte, obligatoire, valide):
    ok, _ = valider_qte(qte, obligatoire=obligatoire)
    assert ok == valide


# ── Note ──────────────────────────────────────────────────────────────────────

def test_valider_note_vide_acceptee():
    ok, _ = valider_note("")
    assert ok is True

def test_valider_note_normale():
    ok, _ = valider_note("Réassort fournisseur Bic")
    assert ok is True

def test_valider_note_max_200():
    ok, _ = valider_note("A" * 200)
    assert ok is True

def test_valider_note_trop_longue():
    ok, _ = valider_note("A" * 201)
    assert ok is False
