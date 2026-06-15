"""
ui/vision_board/view.py
Vue principale du Vision Board - orchestrateur léger.
"""

import os
from typing import Dict, Optional

import customtkinter as ctk
import tkinter as tk

from database import DatabaseManager
from services.goal_service import GoalService
from services.vision_board_service import VisionBoardService
from models.vision_board import VisionItem, FloatingText, TextStyle

from .canvas_renderer import CanvasRenderer
from .interaction_handler import InteractionHandler
from .text_dialog import FloatingTextDialog
from .fullscreen import VisionBoardFullscreen

# Imports des dialogs externes
from ui.vision_board.quran_dialog import QuranAyatDialog
from .add_mood_image_dialog import AddMoodImageDialog


CANVAS_WIDTH = 2000
CANVAS_HEIGHT = 1400
CARD_WIDTH = 280
CARD_HEIGHT = 190


class VisionBoardView(ctk.CTkFrame):
    """Vue Vision Board refactorisée."""

    def __init__(
        self,
        master,
        service: GoalService,
        db_manager: DatabaseManager,
        **kwargs
    ):
        super().__init__(master, fg_color="#F8FAFC", **kwargs)

        self.service = service
        self.db = db_manager
        self.vb_service = VisionBoardService(db_manager)

        self.items: Dict[int, VisionItem] = {}
        self.texts: Dict[int, FloatingText] = {}
        self._next_text_id = 1
        self._next_mood_id = -1

        self.renderer: Optional[CanvasRenderer] = None
        self.interaction: Optional[InteractionHandler] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_canvas()
        self._load_all()

    # ═══════════════════════════════════════════════════
    # CONSTRUCTION UI
    # ═══════════════════════════════════════════════════

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent", height=55)
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(15, 5))
        header.grid_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", pady=8)
        ctk.CTkLabel(
            left, text="✨ Mon Vision Board",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#1E293B"
        ).pack(side="left")
        ctk.CTkLabel(
            left, text="Double-clic = éditer  |  Drag = déplacer",
            font=ctk.CTkFont(size=11), text_color="#94A3B8"
        ).pack(side="left", padx=(12, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", pady=8)

        buttons = [
            ("🕌 Ayat", "#059669", "#047857", self._show_quran_dialog),
            ("🖼️ Plein écran", "#8B5CF6", "#7C3AED", self._enter_fullscreen),
            ("➕ Ajouter image", "#10B981", "#059669", self._open_add_image_dialog),
            ("➕ Ajouter texte", "#3B82F6", "#2563EB", self._add_floating_text),
        ]
        for text, fg, hover, cmd in buttons:
            ctk.CTkButton(
                right, text=text, width=130, height=32, corner_radius=8,
                fg_color=fg, hover_color=hover, text_color="#FFFFFF",
                font=ctk.CTkFont(size=12, weight="bold"), command=cmd
            ).pack(side="left", padx=4)

        ctk.CTkButton(
            right, text="💾", width=36, height=32, corner_radius=8,
            fg_color="#FFFFFF", hover_color="#F1F5F9", text_color="#3B82F6",
            border_width=1, border_color="#E2E8F0", font=ctk.CTkFont(size=14),
            command=self._save
        ).pack(side="left", padx=4)

    def _build_canvas(self) -> None:
        container = ctk.CTkFrame(
            self, fg_color="#FFFFFF", corner_radius=16,
            border_width=1, border_color="#E2E8F0"
        )
        container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(5, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(container, bg="#FAFBFC", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        h_scroll = ctk.CTkScrollbar(container, orientation="horizontal", command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll = ctk.CTkScrollbar(container, orientation="vertical", command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.canvas.configure(
            xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set,
            scrollregion=(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
        )

        self.renderer = CanvasRenderer(self.canvas)
        self.interaction = InteractionHandler(
            self.canvas, self.items, self.texts,
            on_item_select=self._on_item_select,
            on_text_select=self._on_text_select,
            on_item_moved=self._save,
            on_resize=lambda item: self.renderer.redraw_item(item)
        )

    # ═══════════════════════════════════════════════════
    # CHARGEMENT
    # ═══════════════════════════════════════════════════

    def _load_all(self) -> None:
        self._load_items()
        self._load_texts()
        self._load_mood_items()
        if not self.items and not self.texts:
            self._show_empty()

    def _load_items(self) -> None:
        goals = self.service.list_goals()
        goals_with_images = [g for g in goals if g.image_path and os.path.exists(g.image_path)]
        saved = self.vb_service.load_goal_positions()

        for idx, goal in enumerate(goals_with_images):
            s = saved.get(goal.id, {})
            item = VisionItem(
                goal_id=goal.id,
                image_path=goal.image_path,
                title=goal.title,
                x=s.get("pos_x", 40 + (idx % 3) * 320),
                y=s.get("pos_y", 40 + (idx // 3) * 250),
                color=getattr(goal, "color", None) or "#3B82F6",
                width=s.get("width", CARD_WIDTH),
                height=s.get("height", CARD_HEIGHT)
            )
            self.items[goal.id] = item
            self.renderer.draw_item(item)

    def _load_texts(self) -> None:
        saved_texts = self.vb_service.load_texts()
        for st in saved_texts:
            self.texts[st.id] = st
            self._next_text_id = max(self._next_text_id, st.id + 1)
            self.renderer.draw_text(st)

    def _load_mood_items(self) -> None:
        mood_items = self.vb_service.load_mood_items()
        for mi in mood_items:
            if not os.path.exists(mi.image_path):
                print(f"⚠️ Image mood introuvable: {mi.image_path}")
                continue
            self.items[mi.goal_id] = mi
            self._next_mood_id = min(self._next_mood_id, mi.goal_id - 1)
            self.renderer.draw_item(mi)

    def _show_empty(self) -> None:
        self.canvas.create_text(
            CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2,
            text="📸 Ajoutez des images à vos goals\nou générez un Mood Board automatique !",
            font=("Segoe UI", 16), fill="#94A3B8", justify="center"
        )

    # ═══════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════

    def _show_quran_dialog(self) -> None:
        from services.quran_service import QuranService  # import local si pas déjà importé en haut
        dialog = QuranAyatDialog(self, QuranService(), on_ayat_selected=self._add_ayat_text)
        self.wait_window(dialog)

    def _add_ayat_text(self, ayat) -> None:
        print(f"DEBUG - Texte reçu: {repr(ayat.arabic_text)}")

        x = self.canvas.canvasx(self.canvas.winfo_width() / 2) - 250
        y = self.canvas.canvasy(self.canvas.winfo_height() / 2) - 100

        font_path = "assets/fonts/Amiri/Amiri-Regular.ttf"
        font_path = font_path if os.path.exists(font_path) else "Segoe UI"
        style = TextStyle(
            font_family=font_path, font_size=32, bold=False,
            color="#059669", background="#F0FDF4", opacity=230
        )

        text_obj = FloatingText(
            id=self._next_text_id, text=ayat.arabic_text,
            x=x, y=y, style=style
        )
        self._next_text_id += 1
        self.texts[text_obj.id] = text_obj
        self.renderer.draw_text(text_obj)
        self._save()
        self._show_toast("✓ Ayat ajouté")

    def _enter_fullscreen(self) -> None:
        self._save()
        if not self.items and not self.texts:
            self._show_toast("⚠️ Le Vision Board est vide", is_error=True)
            return

        fullscreen = VisionBoardFullscreen(
            master=self.winfo_toplevel(),
            items=self.items, texts=self.texts,
            canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT
        )
        fullscreen.enter()

    def _open_add_image_dialog(self) -> None:
        def on_image_selected(path: str, title: str) -> None:
            mood_id = self._next_mood_id
            self._next_mood_id -= 1

            x = max(10, self.canvas.canvasx(self.canvas.winfo_width() / 2) - 140)
            y = max(10, self.canvas.canvasy(self.canvas.winfo_height() / 2) - 95)

            item = VisionItem(
                goal_id=mood_id, image_path=path, title=title,
                x=x, y=y, width=CARD_WIDTH, height=CARD_HEIGHT,
                color="#3B82F6", rotation=0.0, is_mood_item=True
            )
            self.items[mood_id] = item
            self.renderer.draw_item(item)
            self._save()
            self._show_toast("✓ Image ajoutée")

        dialog = AddMoodImageDialog(self, on_image_selected=on_image_selected)
        self.wait_window(dialog)

    def _add_floating_text(self) -> None:
        dialog = FloatingTextDialog(self)
        self.wait_window(dialog)

        if dialog.result is not None and "delete" not in dialog.result:
            x = self.canvas.canvasx(self.canvas.winfo_width() / 2) - 50
            y = self.canvas.canvasy(self.canvas.winfo_height() / 2) - 20

            text_obj = FloatingText(
                id=self._next_text_id,
                text=dialog.result["text"],
                x=x, y=y,
                style=dialog.result["style"]
            )
            self._next_text_id += 1
            self.texts[text_obj.id] = text_obj
            self.renderer.draw_text(text_obj)
            self._save()

    # ═══════════════════════════════════════════════════
    # SÉLECTION / ÉDITION
    # ═══════════════════════════════════════════════════

    def _on_item_select(self, item: VisionItem, edit_mode: bool = False) -> None:
        if edit_mode:
            if item.is_mood_item:
                self._edit_mood_item(item)
            else:
                self._edit_image_text(item)
        else:
            self.renderer.show_border(item)

    def _on_text_select(self, text_obj: FloatingText, edit_mode: bool = False) -> None:
        if edit_mode:
            self._edit_text(text_obj)
        else:
            self.renderer.show_text_border(text_obj)

    def _edit_text(self, text_obj: FloatingText) -> None:
        dialog = FloatingTextDialog(self, text_obj)
        self.wait_window(dialog)

        if dialog.result is None:
            return
        if "delete" in dialog.result:
            self.renderer.clear_text(text_obj)
            if text_obj.id in self.texts:
                del self.texts[text_obj.id]
            self._save()
            return

        text_obj.text = dialog.result["text"]
        text_obj.style = dialog.result["style"]
        self.renderer.draw_text(text_obj)
        self._save()

    def _edit_mood_item(self, item: VisionItem) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("✏️ Éditer")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#FFFFFF")

        ctk.CTkLabel(dialog, text="Titre:", font=ctk.CTkFont(size=12, weight="bold")).pack(padx=20, pady=(15, 5), anchor="w")
        entry = ctk.CTkEntry(dialog, height=35)
        entry.pack(fill="x", padx=20, pady=5)
        entry.insert(0, item.title)

        def save():
            item.title = entry.get().strip()
            self.renderer.redraw_item(item)
            self._save()
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Annuler", command=dialog.destroy, width=90).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Sauvegarder", command=save, width=120, fg_color="#3B82F6").pack(side="right", padx=5)

    def _edit_image_text(self, item: VisionItem) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"📝 {item.title}")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#FFFFFF")

        ctk.CTkLabel(dialog, text="Texte motivant:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(padx=20, pady=(15, 5), anchor="w")
        entry = ctk.CTkTextbox(dialog, height=50, wrap="word", corner_radius=8, border_width=1, border_color="#E2E8F0", fg_color="#F8FAFC", text_color="#1E293B", font=ctk.CTkFont(size=12))
        entry.pack(fill="x", padx=20, pady=5)
        entry.insert("0.0", self.vb_service.load_motivation_text(item.goal_id))

        def save():
            self.vb_service.save_motivation_text(item.goal_id, entry.get("0.0", "end").strip())
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Annuler", command=dialog.destroy, width=90, fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#475569").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="💾 Sauvegarder", command=save, width=120, fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=5)

    # ═══════════════════════════════════════════════════
    # PERSISTANCE
    # ═══════════════════════════════════════════════════

    def _save(self) -> None:
        self.vb_service.save_board(self.items, self.texts)
        self._show_toast("✓ Sauvegardé")

    # ═══════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════

    def _show_toast(self, text: str, is_error: bool = False) -> None:
        color = "#EF4444" if is_error else "#10B981"
        bg = "#FEE2E2" if is_error else "#FFFFFF"
        toast = ctk.CTkLabel(
            self, text=text, font=ctk.CTkFont(size=11), text_color=color,
            fg_color=bg, corner_radius=6, width=120, height=26
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        self.after(1500 if not is_error else 2000, toast.destroy)
