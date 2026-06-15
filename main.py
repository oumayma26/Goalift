#!/usr/bin/env python3
"""
main.py
Point d'entrée de l'application Goals Manager.
"""

import sys
import os

# Ajouter la racine du projet au path
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ui.main_window import MainWindow


def main():
    """Lance l'application."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
