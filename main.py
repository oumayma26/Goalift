"""
main.py
Point d'entrée avec thème clair forcé.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from ui.theme_manager import ThemeManager
from ui.main_window import MainWindow


def main() -> None:
    ThemeManager.setup_theme()
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()