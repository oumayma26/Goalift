"""
ui/vision_board/interaction_handler.py
Gestionnaire d'interactions souris sur le canvas.
Drag & drop, redimensionnement, double-clic, clic droit.
"""

import tkinter as tk
from typing import Optional, Callable, Dict

from models import VisionItem, FloatingText
from .constants import CANVAS_WIDTH, CANVAS_HEIGHT


class InteractionHandler:
    """
    Gère toutes les interactions souris sur le canvas du Vision Board.
    Pattern Observer : notifie la vue via des callbacks.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        items: Dict[int, VisionItem],
        texts: Dict[int, FloatingText],
        on_item_select: Optional[Callable[[VisionItem], None]] = None,
        on_text_select: Optional[Callable[[FloatingText], None]] = None,
        on_item_moved: Optional[Callable[[], None]] = None,
        on_resize: Optional[Callable[[VisionItem], None]] = None,
    ) -> None:
        self.canvas = canvas
        self.items = items
        self.texts = texts

        self.on_item_select = on_item_select
        self.on_text_select = on_text_select
        self.on_item_moved = on_item_moved
        self.on_resize = on_resize

        # État du drag
        self._dragged_item: Optional[VisionItem] = None
        self._dragged_text: Optional[FloatingText] = None
        self._resizing_item: Optional[VisionItem] = None
        self._drag_offx = 0.0
        self._drag_offy = 0.0
        self._resize_start_x = 0.0
        self._resize_start_y = 0.0
        self._resize_start_w = 0.0
        self._resize_start_h = 0.0

        self._bind_events()

    def _bind_events(self) -> None:
        """Bind les événements souris."""
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._on_right_click)

    # ═══════════════════════════════════════════════════
    # DRAG START
    # ═══════════════════════════════════════════════════

    def _on_drag_start(self, event: tk.Event) -> None:
        """Détecte ce qui est cliqué et initialise le drag."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        clicked = self.canvas.find_closest(cx, cy)
        if not clicked:
            return

        clicked_id = clicked[0]

        # 1. Vérifier resize handle
        for item in self.items.values():
            if item.is_mood_item and hasattr(item, "resize_handles"):
                if clicked_id in item.resize_handles:
                    self._resizing_item = item
                    self._resize_start_x = cx
                    self._resize_start_y = cy
                    self._resize_start_w = item.width
                    self._resize_start_h = item.height
                    return

        # 2. Vérifier texte
        for text_obj in self.texts.values():
            if text_obj.canvas_id == clicked_id:
                self._dragged_text = text_obj
                self._drag_offx = cx - text_obj.x
                self._drag_offy = cy - text_obj.y
                if self.on_text_select:
                    self.on_text_select(text_obj)
                return

        # 3. Vérifier item
        for item in self.items.values():
            if item.canvas_id == clicked_id:
                self._dragged_item = item
                self._drag_offx = cx - item.x
                self._drag_offy = cy - item.y
                if self.on_item_select:
                    self.on_item_select(item)
                return

    # ═══════════════════════════════════════════════════
    # DRAG MOVE
    # ═══════════════════════════════════════════════════

    def _on_drag(self, event: tk.Event) -> None:
        """Gère le mouvement pendant le drag."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # Redimensionnement
        if self._resizing_item:
            self._handle_resize(cx, cy)
            return

        # Texte
        if self._dragged_text:
            self._handle_text_drag(cx, cy)
            return

        # Item
        if self._dragged_item:
            self._handle_item_drag(cx, cy)

    def _handle_resize(self, cx: float, cy: float) -> None:
        """Redimensionne un item mood."""
        item = self._resizing_item
        dx = cx - self._resize_start_x
        dy = cy - self._resize_start_y

        new_w = max(100, min(self._resize_start_w + dx, 600))
        new_h = max(80, min(self._resize_start_h + dy, 450))

        item.width = new_w
        item.height = new_h
        if self.on_resize:
            self.on_resize(item)

    def _handle_text_drag(self, cx: float, cy: float) -> None:
        """Déplace un texte flottant."""
        text_obj = self._dragged_text
        new_x = max(0, min(cx - self._drag_offx, CANVAS_WIDTH - 50))
        new_y = max(0, min(cy - self._drag_offy, CANVAS_HEIGHT - 30))
        dx = new_x - text_obj.x
        dy = new_y - text_obj.y

        self.canvas.move(text_obj.canvas_id, dx, dy)
        if text_obj.bg_id:
            self.canvas.move(text_obj.bg_id, dx, dy)
        text_obj.x = new_x
        text_obj.y = new_y

    def _handle_item_drag(self, cx: float, cy: float) -> None:
        """Déplace un item avec snap sur grille 50px."""
        item = self._dragged_item
        new_x = max(10, min(cx - self._drag_offx, CANVAS_WIDTH - item.width - 10))
        new_y = max(10, min(cy - self._drag_offy, CANVAS_HEIGHT - item.height - 10))
        new_x = round(new_x / 50) * 50
        new_y = round(new_y / 50) * 50
        dx = new_x - item.x
        dy = new_y - item.y

        # Déplacer ombre, image, bordure, handles
        for tag in [item.shadow_id, item.canvas_id]:
            if tag:
                self.canvas.move(tag, dx, dy)
        self.canvas.move(f"border_{item.goal_id}", dx, dy)

        if hasattr(item, "resize_handles"):
            for hid in item.resize_handles:
                self.canvas.move(hid, dx, dy)

        item.x = new_x
        item.y = new_y

    # ═══════════════════════════════════════════════════
    # DRAG STOP
    # ═══════════════════════════════════════════════════

    def _on_drag_stop(self, event: tk.Event) -> None:
        """Termine le drag et notifie."""
        if self._resizing_item:
            self._resizing_item = None
            if self.on_item_moved:
                self.on_item_moved()

        if self._dragged_text:
            self._dragged_text = None
            if self.on_item_moved:
                self.on_item_moved()

        if self._dragged_item:
            self._dragged_item = None
            if self.on_item_moved:
                self.on_item_moved()

    # ═══════════════════════════════════════════════════
    # DOUBLE-CLIC
    # ═══════════════════════════════════════════════════

    def _on_double_click(self, event: tk.Event) -> None:
        """Double-clic = éditer."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        clicked = self.canvas.find_closest(cx, cy)
        if not clicked:
            return

        clicked_id = clicked[0]

        for text_obj in self.texts.values():
            if text_obj.canvas_id == clicked_id:
                if self.on_text_select:
                    self.on_text_select(text_obj, edit_mode=True)
                return

        for item in self.items.values():
            if item.canvas_id == clicked_id:
                if self.on_item_select:
                    self.on_item_select(item, edit_mode=True)
                return

    # ═══════════════════════════════════════════════════
    # CLIC DROIT (menu contextuel)
    # ═══════════════════════════════════════════════════

    def _on_right_click(self, event: tk.Event) -> None:
        """Clic droit = menu contextuel."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        clicked = self.canvas.find_closest(cx, cy)
        if not clicked:
            return

        clicked_id = clicked[0]

        for text_obj in self.texts.values():
            if text_obj.canvas_id == clicked_id:
                self._show_text_menu(event, text_obj)
                return

        for item in self.items.values():
            if item.canvas_id == clicked_id:
                self._show_item_menu(event, item)
                return

    def _show_text_menu(self, event: tk.Event, text_obj: FloatingText) -> None:
        """Menu contextuel pour un texte."""
        menu = tk.Menu(self.canvas, tearoff=0, bg="#FFFFFF", fg="#1E293B",
                       activebackground="#EFF6FF", activeforeground="#3B82F6",
                       font=("Segoe UI", 11))
        menu.add_command(label="✏️ Éditer", 
                         command=lambda: self.on_text_select(text_obj, edit_mode=True) if self.on_text_select else None)
        menu.add_command(label="🗑️ Supprimer",
                         command=lambda: self._delete_text(text_obj))
        menu.tk_popup(event.x_root, event.y_root)

    def _show_item_menu(self, event: tk.Event, item: VisionItem) -> None:
        """Menu contextuel pour un item."""
        menu = tk.Menu(self.canvas, tearoff=0, bg="#FFFFFF", fg="#1E293B",
                       activebackground="#EFF6FF", activeforeground="#3B82F6",
                       font=("Segoe UI", 11))

        if item.is_mood_item:
            menu.add_command(label="✏️ Renommer",
                             command=lambda: self.on_item_select(item, edit_mode=True) if self.on_item_select else None)
            menu.add_command(label="🗑️ Supprimer",
                             command=lambda: self._delete_item(item))
        else:
            menu.add_command(label="✏️ Texte motivant",
                             command=lambda: self.on_item_select(item, edit_mode=True) if self.on_item_select else None)
            menu.add_command(label="👁️ Voir le détail",
                             command=lambda: self._show_goal_detail(item.goal_id))

        menu.tk_popup(event.x_root, event.y_root)

    def _delete_text(self, text_obj: FloatingText) -> None:
        """Supprime un texte (appelé par le menu)."""
        if text_obj.canvas_id:
            self.canvas.delete(text_obj.canvas_id)
        if text_obj.bg_id:
            self.canvas.delete(text_obj.bg_id)
        if text_obj.id in self.texts:
            del self.texts[text_obj.id]
        if self.on_item_moved:
            self.on_item_moved()

    def _delete_item(self, item: VisionItem) -> None:
        """Supprime un item mood (appelé par le menu)."""
        if not item.is_mood_item:
            return
        for tag in [item.canvas_id, item.shadow_id]:
            if tag:
                self.canvas.delete(tag)
        if hasattr(item, "resize_handles"):
            for hid in item.resize_handles:
                self.canvas.delete(hid)
        self.canvas.delete(f"border_{item.goal_id}")
        if item.goal_id in self.items:
            del self.items[item.goal_id]
        if self.on_item_moved:
            self.on_item_moved()

    def _show_goal_detail(self, goal_id: int) -> None:
        """Placeholder - sera connecté par la vue parent."""
        pass
