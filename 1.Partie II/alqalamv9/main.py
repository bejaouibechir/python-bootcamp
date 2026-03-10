# [V9 - Excel] Point d'entrée de l'application Al Qalam Stock Manager.
#
# Nouveautés V9 :
#   - services/excel_service.py : openpyxl — export rapport multi-feuilles + import bon de commande
#   - ExcelService.exporter_rapport_stock() : classeur 3 feuilles colorisé (Catalogue, Ruptures, Stats)
#   - ExcelService.importer_bon_commande()  : lit un .xlsx fournisseur et approvisionne le stock
#   - Nouvel onglet "📊 Excel" : interface export/import avec prévisualisation Treeview
#
# Prérequis : py -3 -m pip install openpyxl customtkinter
#
# Lancement :
#   py -3 main.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import AlQalamApp


def main():
    """Lance l'application Al Qalam Stock Manager V9."""
    app = AlQalamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
