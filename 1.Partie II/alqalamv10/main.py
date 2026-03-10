# [V10 - SQLite] Point d'entrée de l'application Al Qalam Stock Manager.
#
# Nouveautés V10 :
#   - services/database_service.py : sqlite3 stdlib — schéma 2 tables (produits + mouvements)
#   - StockService : persistance SQLite au lieu de JSON, mouvements historisés en base
#   - Migration automatique : stock.json → alqalam.db au 1er lancement
#   - Nouvel onglet "🗄️ Historique" : requêtes filtrées, stats, export CSV
#
# Prérequis : py -3 -m pip install openpyxl customtkinter
# (sqlite3 est dans la bibliothèque standard Python — aucun pip requis)
#
# Lancement :
#   py -3 main.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import AlQalamApp


def main():
    """Lance l'application Al Qalam Stock Manager V10."""
    app = AlQalamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
