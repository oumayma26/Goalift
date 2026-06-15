"""
models/enums.py
Énumérations de l'application.
"""

from enum import Enum


class LayoutType(Enum):
    """Types de layout pour le collage."""
    GRID = "grid"
    MASONRY = "masonry"
    POLAROID = "polaroid"
    WHEEL = "wheel"
    FREEFORM = "freeform"
    SPIRAL = "spiral"
