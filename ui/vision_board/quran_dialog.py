"""
ui/quran_dialog.py
Dialogue pour choisir un ayat du Coran - Arabe uniquement.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
from services.quran_service import QuranService, QuranAyat


class QuranAyatDialog(ctk.CTkToplevel):
    """Dialogue pour sélectionner un ayat du Coran en arabe."""

    def __init__(self, master, quran_service: QuranService, on_ayat_selected: Optional[Callable] = None):
        super().__init__(master)

        self.quran_service = quran_service
        self.on_ayat_selected = on_ayat_selected
        self.selected_ayat: Optional[QuranAyat] = None

        self.title("🕌 Ayat du Coran")
        self.geometry("520x500")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        self._build_ui()
        self._load_random_ayat()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # La zone ayat prend l'espace disponible

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="🕌 Ayat du Coran",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        # Thèmes
        themes_frame = ctk.CTkFrame(self, fg_color="transparent")
        themes_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=5)

        ctk.CTkLabel(
            themes_frame,
            text="Thème :",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#475569"
        ).pack(side="left", padx=(0, 10))

        self.theme_var = ctk.StringVar(value="aleatoire")
        themes = ["aleatoire"] + self.quran_service.get_all_themes()

        self.theme_menu = ctk.CTkOptionMenu(
            themes_frame,
            values=themes,
            variable=self.theme_var,
            width=180,
            height=32,
            fg_color="#F1F5F9",
            button_color="#E2E8F0",
            text_color="#1E293B",
            command=self._on_theme_changed
        )
        self.theme_menu.pack(side="left")

        ctk.CTkButton(
            themes_frame,
            text="🔄",
            width=32, height=32,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            command=self._load_random_ayat
        ).pack(side="left", padx=8)

        # ═══════════════════════════════════════════════════
        # Zone d'affichage de l'ayat - AVEC SCROLLBAR NATIVE
        # ═══════════════════════════════════════════════════
        self.ayat_frame = ctk.CTkFrame(self, fg_color="#F0FDF4", corner_radius=16)
        self.ayat_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=10)
        self.ayat_frame.grid_columnconfigure(0, weight=1)
        self.ayat_frame.grid_rowconfigure(0, weight=1)

        # tk.Text avec scrollbar native tkinter
        self.arabic_text = tk.Text(
            self.ayat_frame,
            wrap="word",
            font=("Scheherazade New", 24),
            fg="#059669",
            bg="#F0FDF4",
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            pady=20,
            height=1,  # S'adapte dynamiquement
            cursor="arrow",
            yscrollcommand=None  # On ajoute la scrollbar après
        )
        self.arabic_text.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # Scrollbar native verticale stylisée
        self.scrollbar = tk.Scrollbar(
            self.ayat_frame,
            orient="vertical",
            command=self.arabic_text.yview,
            bg="#F0FDF4",
            troughcolor="#D1FAE5",
            activebackground="#34D399",
            highlightthickness=0,
            bd=0,
            width=8
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        # Connecter scrollbar ↔ text
        self.arabic_text.config(yscrollcommand=self.scrollbar.set)

        # Configurer l'alignement à droite pour RTL
        self.arabic_text.tag_configure("rtl", justify="right")
        self.arabic_text.config(state="disabled")

        # Référence (sourate + numéro)
        self.reference_label = ctk.CTkLabel(
            self.ayat_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#6B7280",
            fg_color="transparent"
        )
        self.reference_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Boutons
        btn_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        btn_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="Annuler",
            command=self.destroy,
            height=40,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=5)

        self.add_btn = ctk.CTkButton(
            btn_frame,
            text="➕ Ajouter au board",
            command=self._on_add,
            height=40,
            corner_radius=8,
            fg_color="#059669",
            hover_color="#047857",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled"
        )
        self.add_btn.pack(side="right", padx=5)

    def _on_theme_changed(self, theme):
        """Changement de thème."""
        if theme == "aleatoire":
            self._load_random_ayat()
        else:
            self._load_thematic_ayat(theme)

    def _load_random_ayat(self):
        """Charge un ayat aléatoire."""
        self._load_ayat(self.quran_service.get_random_ayat())

    def _load_thematic_ayat(self, theme: str):
        """Charge un ayat thématique."""
        self._load_ayat(self.quran_service.get_ayat_by_theme(theme))

    def _load_ayat(self, ayat: Optional[QuranAyat]):
        """Affiche l'ayat dans le dialogue."""
        if not ayat:
            self.arabic_text.config(state="normal")
            self.arabic_text.delete("1.0", "end")
            self.arabic_text.insert("1.0", "⚠️ Impossible de charger l'ayat", "rtl")
            self.arabic_text.config(state="disabled")
            self.reference_label.configure(text="Vérifiez votre connexion internet")
            self.add_btn.configure(state="disabled")
            return

        self.selected_ayat = ayat

        # Afficher l'ayat en arabe avec tag RTL
        self.arabic_text.config(state="normal")
        self.arabic_text.delete("1.0", "end")
        self.arabic_text.insert("1.0", ayat.arabic_text, "rtl")
        self.arabic_text.config(state="disabled")

        # Scroll en haut pour voir le début
        self.arabic_text.see("1.0")

        # Référence en français pour info
        self.reference_label.configure(
            text=f"Sourate {ayat.surah_name_french} ({ayat.surah_number}) — Ayat {ayat.ayat_number}"
        )

        self.add_btn.configure(state="normal")

    def _on_add(self):
        """Ajoute l'ayat au board."""
        if self.selected_ayat and self.on_ayat_selected:
            self.on_ayat_selected(self.selected_ayat)
        self.destroy()