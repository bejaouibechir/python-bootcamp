"""
generate_csv_inputs.py

Objectif
- Créer automatiquement, dans C:\temp\io, tous les fichiers CSV d'entrée utilisés par l'atelier CSV.
- Éviter de les écrire à la main et garantir que chaque exercice a son input prêt.

Utilisation (Windows)
1) Ouvrir un terminal dans C:\temp\io
2) Lancer :
   python generate_csv_inputs.py

Optionnel
- Changer le dossier de sortie :
   python generate_csv_inputs.py D:\data\io

Résultat
- Le script crée le dossier s'il n'existe pas
- Il écrit tous les fichiers CSV nécessaires (cas01 à cas08, q01 à q15)
- Il affiche la liste des fichiers générés
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def write_text_file(path: Path, content: str) -> None:
    # Écrit en UTF-8 avec des fins de ligne telles que définies dans les contenus ci-dessous
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    # Dossier par défaut (atelier)
    default_out_dir = Path(r"C:\temp\io")

    # Permet de surcharger le dossier de sortie par argument
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_out_dir

    # Important : on garde des contenus au plus proche de l'atelier, y compris certaines particularités
    # (espaces, lignes vides, séparateurs, etc.) afin que les exercices soient reproductibles.
    files: dict[str, str] = {}

    # -----------------------------
    # Cas 1
    # -----------------------------
    files["cas01_header.csv"] = (
        "policyID,statecode,county\n"
        "119736,FL,CLAY COUNTY\n"
        "448094,FL,CLAY COUNTY\n"
        "206893,FL,CLAY COUNTY\n"
    )

    # -----------------------------
    # Cas 2
    # -----------------------------
    files["cas02_dict.csv"] = (
        "policyID,statecode,county\n"
        "333743,FL,CLAY COUNTY\n"
        "172534,FL,SUWANNEE COUNTY\n"
        "995932,FL,PINELLAS COUNTY\n"
    )

    # -----------------------------
    # Cas 3 (délimiteur ; + espaces)
    # -----------------------------
    files["cas03_delim.csv"] = (
        "policyID; statecode; county\n"
        "119736; FL; CLAY COUNTY\n"
        "448094; FL; CLAY COUNTY\n"
        "206893; FL; CLAY COUNTY\n"
    )

    # -----------------------------
    # Cas 4 (types + valeurs invalides)
    # -----------------------------
    files["cas04_types.csv"] = (
        "policyID,tiv_2011,tiv_2012\n"
        "119736,498960,792148.9\n"
        "448094,1322376.3,1438163.57\n"
        "206893,ABC,192476.78\n"
        "333743,79520.76,\n"
    )

    # -----------------------------
    # Cas 5 (structure invalide : colonnes manquantes)
    # -----------------------------
    files["cas05_invalide.csv"] = (
        "policyID,statecode\n"
        "119736,FL\n"
        "448094,FL\n"
    )

    # -----------------------------
    # Cas 6 (variation > 20%)
    # -----------------------------
    files["cas06_variation.csv"] = (
        "policyID,tiv_2011,tiv_2012\n"
        "119736,498960,792148.9\n"
        "448094,1322376.3,1438163.57\n"
        "206893,190724.4,192476.78\n"
        "333743,79520.76,86854.48\n"
        "172534,254281.5,246144.49\n"
    )

    # -----------------------------
    # Cas 7 (export filtré)
    # -----------------------------
    files["cas07_export_source.csv"] = (
        "policyID,county,tiv_2012\n"
        "119736,CLAY COUNTY,792148.9\n"
        "448094,CLAY COUNTY,1438163.57\n"
        "206893,CLAY COUNTY,192476.78\n"
        "333743,CLAY COUNTY,86854.48\n"
        "142071,PINELLAS COUNTY,1200000\n"
    )

    # -----------------------------
    # Cas 8 (pandas)
    # -----------------------------
    files["cas08_pandas.csv"] = (
        "policyID,county,tiv_2012\n"
        "119736,CLAY COUNTY,792148.9\n"
        "448094,CLAY COUNTY,1438163.57\n"
        "206893,CLAY COUNTY,192476.78\n"
        "995932,PINELLAS COUNTY,206393.76\n"
        "142071,PINELLAS COUNTY,1200000\n"
    )

    # =============================
    # Questions (q01 à q15)
    # =============================

    # q01
    files["q01_source.csv"] = (
        "id,nom\n"
        "1,Alice\n"
        "2,Bob\n"
    )

    # q02
    files["q02_columns.csv"] = (
        "nom,age\n"
        "Alice,30\n"
        "Bob,25\n"
    )

    # q03
    files["q03_missing_column.csv"] = (
        "nom\n"
        "Alice\n"
        "Bob\n"
    )

    # q04 (ligne vide volontaire au milieu)
    files["q04_empty_lines.csv"] = (
        "id,nom\n"
        "1,Alice\n"
        "\n"
        "2,Bob\n"
    )

    # q05 (accents)
    files["q05_encoding.csv"] = (
        "nom\n"
        "Élodie\n"
        "André\n"
    )

    # q06
    files["q06_zero.csv"] = (
        "id,valeur1,valeur2\n"
        "1,0,100\n"
        "2,50,100\n"
    )

    # q07 (décimale avec virgule ; contenu gardé tel que l'atelier)
    files["q07_decimal.csv"] = (
        "montant\n"
        "12,5\n"
    )

    # q08
    files["q08_limit.csv"] = (
        "id\n"
        "1\n"
        "2\n"
        "3\n"
        "4\n"
        "5\n"
        "6\n"
        "7\n"
    )

    # q09
    files["q09_count.csv"] = (
        "id\n"
        "1\n"
        "2\n"
        "3\n"
        "4\n"
    )

    # q10
    files["q10_sort.csv"] = (
        "nom,age\n"
        "Alice,30\n"
        "Bob,25\n"
        "Claire,35\n"
    )

    # q11
    files["q11_filter.csv"] = (
        "nom,age,pays\n"
        "Alice,30,FR\n"
        "Bob,25,FR\n"
        "Claire,35,US\n"
    )

    # q12 (age vide)
    files["q12_nan.csv"] = (
        "nom,age\n"
        "Alice,30\n"
        "Bob,\n"
        "Claire,35\n"
    )

    # q13 (espaces invisibles)
    files["q13_spaces.csv"] = (
        "nom\n"
        " Alice\n"
        "Bob \n"
    )

    # q14
    files["q14_group.csv"] = (
        "county,valeur\n"
        "A,100\n"
        "A,200\n"
        "B,300\n"
    )

    # q15
    files["q15_source.csv"] = (
        "id,nom,age\n"
        "1,Alice,30\n"
        "2,Bob,25\n"
    )

    # -----------------------------
    # Écriture sur disque
    # -----------------------------
    created = []
    for filename, content in files.items():
        target = out_dir / filename
        write_text_file(target, content)
        created.append(target)

    # Affichage final
    print("Dossier de sortie :", str(out_dir))
    print("Fichiers CSV générés :", len(created))
    for p in created:
        print(" -", p)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())