"""Validation et normalisation par regex."""

from __future__ import annotations

import re
from dataclasses import dataclass

RE_REF = re.compile(r"^(?P<famille>[A-Z]{2,6})-(?P<numero>\d{3,6})$")
RE_PRIX = re.compile(r"^\d{1,6}([.,]\d{1,2})?$")
RE_QTE = re.compile(r"^\d{1,6}$")
RE_NOM = re.compile(r"^[\w\sÀ-ÿ\-]{2,60}$")
RE_LOG = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \| (?P<niveau>\w+) \| (?P<message>.+)"
)


@dataclass
class ResultatValidation:
    valide: bool
    message: str = ""


def valider_ref(ref: str) -> ResultatValidation:
    ref = ref.strip().upper()
    if not ref:
        return ResultatValidation(False, "La référence est obligatoire")
    if not RE_REF.match(ref):
        return ResultatValidation(False, "Format attendu : FAMILLE-NUMERO (ex: CRAY-001)")
    return ResultatValidation(True)


def valider_prix(prix: str) -> ResultatValidation:
    prix = prix.strip().replace(" ", "")
    if not prix:
        return ResultatValidation(False, "Le prix est obligatoire")
    if not RE_PRIX.match(prix):
        return ResultatValidation(False, "Prix invalide (ex: 1.50 ou 1,50)")
    return ResultatValidation(True)


def valider_qte(qte: str) -> ResultatValidation:
    qte = qte.strip()
    if not qte:
        return ResultatValidation(False, "La quantité est obligatoire")
    if not RE_QTE.match(qte):
        return ResultatValidation(False, "Quantité invalide (entier positif)")
    return ResultatValidation(True)


def normaliser_prix(prix: str) -> float:
    return float(prix.strip().replace(" ", "").replace(",", "."))


def normaliser_ref(ref: str) -> str:
    ref = ref.strip().upper().replace("_", "-").replace(" ", "")
    if "-" not in ref and len(ref) >= 5:
        ref = f"{ref[:-3]}-{ref[-3:]}"
    return ref


def rechercher_dans_logs(pattern: str, lignes: list[str]) -> list[str]:
    try:
        re_pattern = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"Pattern regex invalide : {exc}") from exc
    return [ligne for ligne in lignes if re_pattern.search(ligne)]
