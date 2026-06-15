"""
models/vision_board.py
Modèles de données pour le Vision Board.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TextStyle:
    """Style de texte flottant."""
    font_family: str = "Arial"
    font_size: int = 16
    bold: bool = False
    italic: bool = False
    color: str = "#1E293B"
    background: Optional[str] = None
    opacity: int = 0


@dataclass
class FloatingText:
    """Texte flottant sur le Vision Board."""
    id: int
    text: str
    x: float
    y: float
    style: TextStyle = field(default_factory=TextStyle)
    # Champs renderer (non persistés)
    canvas_id: Optional[int] = field(default=None, repr=False)
    bg_id: Optional[int] = field(default=None, repr=False)
    tk_image: Optional[object] = field(default=None, repr=False)


@dataclass
class VisionItem:
    """Item affiché sur le Vision Board (goal ou mood)."""
    goal_id: int
    image_path: str
    title: str
    x: float = 0
    y: float = 0
    width: float = 280
    height: float = 190
    color: str = "#3B82F6"
    rotation: float = 0.0
    is_mood_item: bool = False
    # Champs renderer (non persistés)
    canvas_id: Optional[int] = field(default=None, repr=False)
    shadow_id: Optional[int] = field(default=None, repr=False)
    tk_image: Optional[object] = field(default=None, repr=False)
    resize_handles: list = field(default_factory=list, repr=False)
