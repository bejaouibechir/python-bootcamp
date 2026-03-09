# [V6 - Métaclasses] Point d'entrée de l'application Al Qalam Stock Manager.
#
# Nouveautés V6 :
#   - StockService est un Singleton (SingletonMeta) : une seule instance garantie
#   - Les mouvements de stock utilisent un registre automatique (RegistreMouvementMeta)
#   - 4 types de mouvements : EntreeMouvement, SortieMouvement,
#                             AjustementMouvement, RetourMouvement
#   - Nouvel onglet "🗂 Registre" : visualise le registre et démontre le Singleton
#
# Lancement :
#   py -3 main.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import AlQalamApp


def main():
    """Lance l'application Al Qalam Stock Manager V6."""
    app = AlQalamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
