"""
services/vision_board_service.py
Service de persistance du Vision Board.
Gère TOUTES les opérations DB liées au Vision Board.
"""

import sqlite3
from typing import Optional, List, Dict
from dataclasses import asdict

from database.database import DatabaseManager
from models.vision_board import VisionItem, FloatingText, TextStyle

class VisionBoardService:
    """
    Service de persistance du Vision Board.
    Responsabilité unique : lire/écrire les données du board en DB.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Vérifie que les tables existent (créées par database.py + migrations)."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('vision_board', 'vision_board_texts', 'vision_board_mood')
            """)
            existing = {row[0] for row in cursor.fetchall()}
            required = {"vision_board", "vision_board_texts", "vision_board_mood"}
            if missing := required - existing:
                raise RuntimeError(
                    f"Tables manquantes : {missing}. "
                    "Lancez database.py et les migrations d'abord."
                )

    # ═══════════════════════════════════════════════════
    # GOALS (positions)
    # ═══════════════════════════════════════════════════

    def save_goal_positions(self, items: Dict[int, VisionItem]) -> None:
        """Sauvegarde les positions des goals (non mood)."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            for item in items.values():
                if item.is_mood_item:
                    continue
                cursor.execute("""
                    INSERT INTO vision_board (goal_id, pos_x, pos_y, width, height)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(goal_id) DO UPDATE SET
                        pos_x = excluded.pos_x,
                        pos_y = excluded.pos_y,
                        width = excluded.width,
                        height = excluded.height
                """, (item.goal_id, item.x, item.y, item.width, item.height))
            conn.commit()

    def load_goal_positions(self) -> Dict[int, dict]:
        """Charge les positions sauvegardées des goals."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT goal_id, pos_x, pos_y, width, height FROM vision_board"
                )
                return {
                    row[0]: {
                        "pos_x": row[1] or 0,
                        "pos_y": row[2] or 0,
                        "width": row[3] or 280,
                        "height": row[4] or 190
                    }
                    for row in cursor.fetchall()
                }
        except sqlite3.OperationalError:
            return {}

    def save_motivation_text(self, goal_id: int, text: str) -> None:
        """Sauvegarde le texte motivant d'un goal."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vision_board (goal_id, motivation_text)
                VALUES (?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                    motivation_text = excluded.motivation_text
            """, (goal_id, text))
            conn.commit()

    def load_motivation_text(self, goal_id: int) -> str:
        """Charge le texte motivant d'un goal."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT motivation_text FROM vision_board WHERE goal_id = ?",
                    (goal_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else ""
        except sqlite3.OperationalError:
            return ""

    # ═══════════════════════════════════════════════════
    # TEXTES FLOTTANTS
    # ═══════════════════════════════════════════════════

    def save_texts(self, texts: Dict[int, FloatingText]) -> None:
        """Sauvegarde tous les textes flottants."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vision_board_texts")
            for text_obj in texts.values():
                cursor.execute("""
                    INSERT INTO vision_board_texts
                    (id, text, x, y, font_family, font_size, bold, italic, color, background, opacity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    text_obj.id, text_obj.text, text_obj.x, text_obj.y,
                    text_obj.style.font_family, text_obj.style.font_size,
                    int(text_obj.style.bold), int(text_obj.style.italic),
                    text_obj.style.color, text_obj.style.background,
                    text_obj.style.opacity
                ))
            conn.commit()

    def load_texts(self) -> List[FloatingText]:
        """Charge tous les textes flottants."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vision_board_texts")
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                texts = []
                for row in rows:
                    style = TextStyle(
                        font_family=row.get("font_family", "Arial"),
                        font_size=row.get("font_size", 16),
                        bold=bool(row.get("bold", 0)),
                        italic=bool(row.get("italic", 0)),
                        color=row.get("color", "#1E293B"),
                        background=row.get("background"),
                        opacity=row.get("opacity", 0)
                    )
                    texts.append(FloatingText(
                        id=row["id"],
                        text=row["text"],
                        x=row.get("x", 100),
                        y=row.get("y", 100),
                        style=style
                    ))
                return texts
        except sqlite3.OperationalError:
            return []

    # ═══════════════════════════════════════════════════
    # MOOD ITEMS
    # ═══════════════════════════════════════════════════

    def save_mood_items(self, items: Dict[int, VisionItem]) -> None:
        """Sauvegarde les items mood (remplace tout)."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vision_board_mood")
            for item in items.values():
                if not item.is_mood_item:
                    continue
                cursor.execute("""
                    INSERT INTO vision_board_mood
                    (id, image_path, title, x, y, width, height, color, rotation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.goal_id, item.image_path, item.title,
                    item.x, item.y, item.width, item.height,
                    item.color, item.rotation
                ))
            conn.commit()

    def load_mood_items(self) -> List[VisionItem]:
        """Charge les items mood."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vision_board_mood")
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                items = []
                for row in rows:
                    path = row["image_path"]
                    if not path.startswith("/") and not path.startswith("C:"):
                        import os
                        path = os.path.abspath(path)

                    items.append(VisionItem(
                        goal_id=row["id"],
                        image_path=path,
                        title=row.get("title", ""),
                        x=row.get("x", 100),
                        y=row.get("y", 100),
                        width=row.get("width", 280),
                        height=row.get("height", 190),
                        color=row.get("color", "#3B82F6"),
                        rotation=row.get("rotation", 0.0),
                        is_mood_item=True
                    ))
                return items
        except sqlite3.OperationalError:
            return []

    def delete_mood_item(self, mood_id: int) -> None:
        """Supprime un item mood de la DB."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vision_board_mood WHERE id = ?", (mood_id,))
            conn.commit()

    # ═══════════════════════════════════════════════════
    # SAUVEGARDE COMPLÈTE
    # ═══════════════════════════════════════════════════

    def save_board(self, items: Dict[int, VisionItem], texts: Dict[int, FloatingText]) -> None:
        """Sauvegarde complète du board."""
        self.save_goal_positions(items)
        self.save_mood_items(items)
        self.save_texts(texts)
