# [V11 - Tests] Point d'entrée de l'application Al Qalam Stock Manager.
#
# Nouveautés V11 :
#   - Suite de tests pytest dans tests/ : 6 fichiers, >40 cas de test
#   - Couverture mesurée avec pytest-cov (objectif >= 80%)
#   - conftest.py : fixtures partagées (db_vide, stock_vide, produit_demo)
#   - Démonstration : fixtures, parametrize, raises, tmp_path, monkeypatch
#
# Prérequis : py -3 -m pip install openpyxl customtkinter pytest pytest-cov
#
# Lancement application :
#   py -3 main.py
#
# Lancement tests :
#   py -3 -m pytest tests/ -v
#   py -3 -m pytest tests/ --cov=. --cov-report=term-missing

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import AlQalamApp


def main():
    """Lance l'application Al Qalam Stock Manager V11."""
    app = AlQalamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
