"""
ui/theme_manager.py
Gestionnaire de thème - FORCÉ CLAIR.
"""

import customtkinter as ctk
import json
import os
from typing import Literal


class ThemeManager:
    """
    Gestionnaire de thème - Mode clair par défaut.
    """

    CONFIG_FILE = "theme_config.json"

    # Palette de couleurs claires personnalisée
    COLORS = {
        "bg_primary": "#F8FAFC",      # Fond principal très clair
        "bg_secondary": "#FFFFFF",     # Fond cartes/panneaux
        "bg_card": "#FFFFFF",          # Fond des cartes
        "border": "#E2E8F0",         # Bordures subtiles
        "text_primary": "#1E293B",   # Texte principal (presque noir)
        "text_secondary": "#64748B", # Texte secondaire (gris)
        "accent": "#3B82F6",         # Bleu principal
        "accent_hover": "#2563EB",   # Bleu survol
        "success": "#10B981",        # Vert succès
        "warning": "#F59E0B",        # Orange avertissement
        "danger": "#EF4444",         # Rouge erreur
        "priority_high": "#EF4444",  # Priorité haute
        "priority_medium": "#F59E0B",# Priorité moyenne
        "priority_low": "#10B981",   # Priorité basse
    }

    @classmethod
    def setup_theme(cls) -> None:
        """Configure le thème clair au démarrage."""
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

    @classmethod
    def get_color(cls, key: str) -> str:
        """Récupère une couleur de la palette."""
        return cls.COLORS.get(key, "#000000")

    @classmethod
    def set_theme(cls, theme: Literal["Light", "Dark", "System"]) -> None:
        """Force toujours le thème clair."""
        ctk.set_appearance_mode("Light")
        try:
            with open(cls.CONFIG_FILE, "w") as f:
                json.dump({"theme": "Light"}, f)
        except IOError:
            pass

    @classmethod
    def get_current_theme(cls) -> str:
        """Retourne toujours Light."""
        return "Light"