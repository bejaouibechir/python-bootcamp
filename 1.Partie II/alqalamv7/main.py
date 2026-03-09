# [V7 - Regex] Point d'entrée de l'application Al Qalam Stock Manager.
#
# Nouveautés V7 :
#   - Module validators/ : patterns regex compilés pour validation formulaires
#   - Dialogues : validation en temps réel (<KeyRelease>) avec feedback ✓/✗ coloré
#   - services/log_parser.py : convertit le journal en texte, l'analyse par regex
#   - Nouvel onglet "🔍 Analyseur" : stats par regex, recherche regex interactive
#
# Lancement :
#   py -3 main.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import AlQalamApp


def main():
    """Lance l'application Al Qalam Stock Manager V7."""
    app = AlQalamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
