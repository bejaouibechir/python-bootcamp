"""Import et export CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from config import REQUIRED_CSV_COLUMNS
from alq_io.validator import normaliser_prix, normaliser_ref, valider_ref
from models.produit import Produit


@dataclass
class RapportImport:
    importes: int = 0
    mis_a_jour: int = 0
    rejetes: int = 0
    erreurs: list[str] = field(default_factory=list)

    def __str__(self):
        return (
            f"Import terminé : {self.importes} importés | "
            f"{self.mis_a_jour} mis à jour | {self.rejetes} rejetés"
        )


def importer_catalogue(chemin: str, stock_service) -> RapportImport:
    rapport = RapportImport()
    path = Path(chemin)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        lecteur = csv.DictReader(handle)
        colonnes_presentes = set(lecteur.fieldnames or [])
        manquantes = set(REQUIRED_CSV_COLUMNS) - colonnes_presentes
        if manquantes:
            raise ValueError(f"Colonnes manquantes : {sorted(manquantes)}")

        for num_ligne, ligne in enumerate(lecteur, start=2):
            try:
                produit = _ligne_vers_produit(ligne)
                if produit.ref in stock_service:
                    stock_service.mettre_a_jour_produit(produit)
                    rapport.mis_a_jour += 1
                else:
                    stock_service.ajouter_produit(produit)
                    rapport.importes += 1
            except Exception as exc:
                rapport.rejetes += 1
                rapport.erreurs.append(f"Ligne {num_ligne}: {exc}")

    return rapport


def _ligne_vers_produit(ligne: dict) -> Produit:
    ref = normaliser_ref(ligne.get("ref", ""))
    if not valider_ref(ref).valide:
        raise ValueError(f"Référence invalide : {ref!r}")

    return Produit(
        ref=ref,
        nom=ligne["nom"].strip(),
        categorie=ligne["categorie"].strip(),
        prix_achat=normaliser_prix(str(ligne["prix_achat"])),
        prix_vente=normaliser_prix(str(ligne["prix_vente"])),
        qte=int(str(ligne["qte"]).strip()),
        seuil_min=int(str(ligne["seuil_min"]).strip()),
    )


def exporter_stock(chemin: str, stock_service) -> int:
    colonnes = ["ref", "nom", "categorie", "prix_achat", "prix_vente", "qte", "seuil_min"]
    nb = 0
    with open(chemin, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=colonnes)
        writer.writeheader()
        for produit in sorted(stock_service):
            writer.writerow({k: produit.to_dict()[k] for k in colonnes})
            nb += 1
    return nb

