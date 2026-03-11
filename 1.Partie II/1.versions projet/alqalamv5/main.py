# [V5 - Décorateurs] main.py est le seul fichier à exécuter.
# Il initialise l'application et démarre la boucle graphique.

import sys
from pathlib import Path

# Ajoute le dossier racine au chemin Python pour les imports relatifs
sys.path.insert(0, str(Path(__file__).parent))

from ui.app import AlQalamApp


def main():
    """Lance l'application Al Qalam Stock Manager."""
    app = AlQalamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
