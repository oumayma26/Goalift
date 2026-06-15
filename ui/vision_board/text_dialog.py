"""
ui/vision_board/text_dialog.py
Dialogue d'édition de texte flottant.
"""

import tkinter as tk
from tkinter import colorchooser
from typing import Optional

import customtkinter as ctk

from models import FloatingText, TextStyle


class FloatingTextDialog(ctk.CTkToplevel):
    """Dialogue pour créer/éditer un texte flottant."""

    def __init__(self, master, text_obj: Optional[FloatingText] = None):
        super().__init__(master)
        self.title("✏️ Texte libre")
        self.geometry("450x580")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        self.result = None
        self.text_obj = text_obj

        self._center_on_master(master)
        self._build_ui()

    def _center_on_master(self, master) -> None:
        """Centre le dialogue sur la fenêtre parent."""
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 450) // 2
        y = master.winfo_y() + (master.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Construit l'interface du dialogue."""
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="#FFFFFF", corner_radius=0,
            scrollbar_fg_color="#E2E8F0",
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color="#94A3B8"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        content = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF")
        content.pack(fill="x", expand=True)

        self._build_header(content)
        self._build_text_section(content)
        self._build_font_section(content)
        self._build_color_section(content)
        self._build_buttons(content)

    def _build_header(self, parent) -> None:
        ctk.CTkLabel(
            parent, text="✨ Texte libre",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(15, 10), padx=20, anchor="w")

    def _build_text_section(self, parent) -> None:
        ctk.CTkLabel(
            parent, text="Contenu:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(10, 5))

        self.text_entry = ctk.CTkTextbox(
            parent, height=60, wrap="word",
            corner_radius=8, border_width=1, border_color="#E2E8F0",
            fg_color="#F8FAFC", text_color="#1E293B",
            font=ctk.CTkFont(size=13)
        )
        self.text_entry.pack(fill="x", padx=20, pady=5)
        default_text = self.text_obj.text if self.text_obj else "Votre texte ici"
        self.text_entry.insert("0.0", default_text)

    def _build_font_section(self, parent) -> None:
        font_frame = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=10)
        font_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            font_frame, text="📝 Police",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=12, pady=(10, 5))

        # Police
        row1 = ctk.CTkFrame(font_frame, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(row1, text="Police:", font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left", padx=(0, 8))

        fonts = ["Arial", "Times New Roman", "Courier New", "Georgia", "Verdana",
                 "Helvetica", "Impact", "Comic Sans MS", "Segoe UI", "Tahoma"]
        self.font_var = ctk.StringVar(value=self.text_obj.style.font_family if self.text_obj else "Arial")
        ctk.CTkOptionMenu(
            row1, values=fonts, variable=self.font_var, width=180, height=28,
            fg_color="#FFFFFF", button_color="#E2E8F0", text_color="#1E293B",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")

        # Taille
        row2 = ctk.CTkFrame(font_frame, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(row2, text="Taille:", font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left", padx=(0, 8))

        self.size_slider = ctk.CTkSlider(row2, from_=8, to=72, number_of_steps=64, width=100)
        self.size_slider.set(self.text_obj.style.font_size if self.text_obj else 16)
        self.size_slider.pack(side="left")
        self.size_label = ctk.CTkLabel(row2, text=str(self.text_obj.style.font_size if self.text_obj else 16),
                                       width=30, font=ctk.CTkFont(size=11))
        self.size_label.pack(side="left", padx=5)
        self.size_slider.configure(command=lambda v: self.size_label.configure(text=f"{int(v)}"))

        # Gras / Italique
        row3 = ctk.CTkFrame(font_frame, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=(5, 10))
        self.bold_var = ctk.BooleanVar(value=self.text_obj.style.bold if self.text_obj else False)
        ctk.CTkCheckBox(row3, text="Gras", variable=self.bold_var, font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
        self.italic_var = ctk.BooleanVar(value=self.text_obj.style.italic if self.text_obj else False)
        ctk.CTkCheckBox(row3, text="Italique", variable=self.italic_var, font=ctk.CTkFont(size=11)).pack(side="left", padx=8)

    def _build_color_section(self, parent) -> None:
        color_frame = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=10)
        color_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            color_frame, text="🎨 Couleurs",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", padx=12, pady=(10, 5))

        # Couleur texte
        row_c1 = ctk.CTkFrame(color_frame, fg_color="transparent")
        row_c1.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(row_c1, text="Texte:", font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left", padx=(0, 10))

        self.text_color = self.text_obj.style.color if self.text_obj else "#1E293B"
        self.text_color_preview = ctk.CTkFrame(
            row_c1, width=28, height=28, corner_radius=6,
            fg_color=self.text_color, border_width=2, border_color="#E2E8F0"
        )
        self.text_color_preview.pack(side="left")
        ctk.CTkButton(
            row_c1, text="Choisir", width=80, height=26, corner_radius=6,
            fg_color="#FFFFFF", hover_color="#F1F5F9", text_color="#475569",
            border_width=1, border_color="#E2E8F0", font=ctk.CTkFont(size=11),
            command=lambda: self._pick_color("text")
        ).pack(side="left", padx=10)

        # Couleur fond
        row_c2 = ctk.CTkFrame(color_frame, fg_color="transparent")
        row_c2.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(row_c2, text="Fond:", font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left", padx=(0, 10))

        self.bg_color = self.text_obj.style.background if self.text_obj else None
        bg_hex = self.bg_color if self.bg_color else "#FFFFFF"
        self.bg_color_preview = ctk.CTkFrame(
            row_c2, width=28, height=28, corner_radius=6,
            fg_color=bg_hex, border_width=2, border_color="#E2E8F0"
        )
        self.bg_color_preview.pack(side="left")
        ctk.CTkButton(
            row_c2, text="Choisir", width=80, height=26, corner_radius=6,
            fg_color="#FFFFFF", hover_color="#F1F5F9", text_color="#475569",
            border_width=1, border_color="#E2E8F0", font=ctk.CTkFont(size=11),
            command=lambda: self._pick_color("bg")
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            row_c2, text="Aucun", width=60, height=26, corner_radius=6,
            fg_color="#FEE2E2", hover_color="#FECACA", text_color="#DC2626",
            font=ctk.CTkFont(size=11), command=self._clear_bg
        ).pack(side="left", padx=5)

        # Opacité
        row_c3 = ctk.CTkFrame(color_frame, fg_color="transparent")
        row_c3.pack(fill="x", padx=12, pady=(5, 10))
        ctk.CTkLabel(row_c3, text="Opacité:", font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left", padx=(0, 8))
        self.opacity_slider = ctk.CTkSlider(row_c3, from_=0, to=255, number_of_steps=51, width=100)
        self.opacity_slider.set(self.text_obj.style.opacity if self.text_obj else 0)
        self.opacity_slider.pack(side="left")
        self.opacity_label = ctk.CTkLabel(row_c3, text=str(self.text_obj.style.opacity if self.text_obj else 0),
                                          width=30, font=ctk.CTkFont(size=11))
        self.opacity_label.pack(side="left", padx=5)
        self.opacity_slider.configure(command=lambda v: self.opacity_label.configure(text=f"{int(v)}"))

    def _build_buttons(self, parent) -> None:
        ctk.CTkFrame(parent, height=1, fg_color="#E2E8F0").pack(fill="x", padx=20, pady=10)

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 20))

        if self.text_obj:
            ctk.CTkButton(
                btn_frame, text="🗑️ Supprimer", width=100,
                fg_color="#FEE2E2", hover_color="#FECACA", text_color="#DC2626",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self._on_delete
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Annuler", width=90,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame, text="💾 Appliquer", width=120,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_save
        ).pack(side="right", padx=5)

    def _pick_color(self, which: str) -> None:
        """Ouvre le sélecteur de couleur."""
        current = self.text_color if which == "text" else (self.bg_color or "#FFFFFF")
        color = colorchooser.askcolor(color=current, title="Couleur")
        if color[1]:
            if which == "text":
                self.text_color = color[1]
                self.text_color_preview.configure(fg_color=color[1])
            else:
                self.bg_color = color[1]
                self.bg_color_preview.configure(fg_color=color[1])

    def _clear_bg(self) -> None:
        """Supprime la couleur de fond."""
        self.bg_color = None
        self.bg_color_preview.configure(fg_color="#FFFFFF")

    def _on_save(self) -> None:
        """Sauvegarde et ferme."""
        self.result = {
            "text": self.text_entry.get("0.0", "end").strip(),
            "style": TextStyle(
                font_family=self.font_var.get(),
                font_size=int(self.size_slider.get()),
                bold=self.bold_var.get(),
                italic=self.italic_var.get(),
                color=self.text_color,
                background=self.bg_color,
                opacity=int(self.opacity_slider.get())
            )
        }
        self.destroy()

    def _on_delete(self) -> None:
        """Marque pour suppression."""
        self.result = {"delete": True}
        self.destroy()
