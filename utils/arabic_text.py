"""
utils/arabic_text.py
Gestion du texte arabe : reshape, BIDI, et rendu RTL pour tkinter/customtkinter.
"""

import os
import platform
from typing import Optional

import customtkinter as ctk
import tkinter as tk

_ARABIC_RESHAPER_AVAILABLE = False
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════
# WINDOWS RTL API
# ═══════════════════════════════════════════════════

def set_windows_rtl(widget):
    """
    Configure un widget tkinter en mode RTL natif (Windows uniquement).
    Cela résout le problème de copier-coller arabe inversé.
    """
    if platform.system() != "Windows":
        return

    try:
        import ctypes
        from ctypes import wintypes

        GWL_EXSTYLE = -20
        WS_EX_RTLREADING = 0x2000
        WS_EX_RIGHT = 0x1000
        WS_EX_LAYOUTRTL = 0x400000

        hwnd = int(widget.winfo_id())
        user32 = ctypes.windll.user32
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            exstyle | WS_EX_RTLREADING | WS_EX_RIGHT | WS_EX_LAYOUTRTL
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════
# FONCTIONS DE TRAITEMENT ARABE
# ═══════════════════════════════════════════════════

def is_arabic(text: str) -> bool:
    """Détecte si le texte contient des caractères arabes."""
    if not text:
        return False
    return any(
        "\u0600" <= c <= "\u06FF" or
        "\u0750" <= c <= "\u077F" or
        "\u08A0" <= c <= "\u08FF" or
        "\uFB50" <= c <= "\uFDFF" or
        "\uFE70" <= c <= "\uFEFF"
        for c in text
    )


def reshape_arabic(text: str) -> str:
    """Reshape + BIDI le texte arabe pour affichage correct en LTR."""
    if not text or not _ARABIC_RESHAPER_AVAILABLE:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        display = get_display(reshaped)
        return display
    except Exception:
        return text


def prepare_for_display(text: str) -> str:
    """Prépare le texte pour l'affichage (reshape + BIDI si arabe)."""
    if not text:
        return text
    if is_arabic(text) and _ARABIC_RESHAPER_AVAILABLE:
        return reshape_arabic(text)
    return text


def reverse_for_storage(text: str) -> str:
    """Convertit le texte visuel en texte logique pour stockage DB."""
    if not text or not _ARABIC_RESHAPER_AVAILABLE:
        return text
    if not is_arabic(text):
        return text
    try:
        logical = get_display(text)
        return logical
    except Exception:
        return text


# ═══════════════════════════════════════════════════
# WIDGETS ARABES — AFFICHAGE
# ═══════════════════════════════════════════════════

class ArabicTextMixin:
    """Mixin pour reshape automatique du texte."""

    def __init__(self, *args, **kwargs):
        self._original_text = kwargs.get("text", "")
        if "text" in kwargs and is_arabic(kwargs["text"]):
            kwargs["text"] = prepare_for_display(kwargs["text"])
        super().__init__(*args, **kwargs)

    def set_text(self, text: str) -> None:
        self._original_text = text
        display_text = prepare_for_display(text)
        if hasattr(self, "configure"):
            self.configure(text=display_text)

    def get_original_text(self) -> str:
        return self._original_text


class ArabicCTkLabel(ctk.CTkLabel, ArabicTextMixin):
    pass


class ArabicCTkButton(ctk.CTkButton, ArabicTextMixin):
    pass


class ArabicCTkOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, *args, **kwargs):
        values = kwargs.get("values", [])
        self._original_values = list(values)
        kwargs["values"] = [prepare_for_display(v) for v in values]
        super().__init__(*args, **kwargs)

    def set_values(self, values: list) -> None:
        self._original_values = list(values)
        super().set_values([prepare_for_display(v) for v in values])

    def get_original_value(self) -> Optional[str]:
        current = self.get()
        for orig, disp in zip(self._original_values, self.cget("values")):
            if disp == current:
                return orig
        return current


class ArabicCTkRadioButton(ctk.CTkRadioButton, ArabicTextMixin):
    pass


class ArabicCTkCheckBox(ctk.CTkCheckBox, ArabicTextMixin):
    pass


# ═══════════════════════════════════════════════════
# WIDGET ARABE — SAISIE (Entry RTL natif Windows)
# ═══════════════════════════════════════════════════

class ArabicCTkEntry(ctk.CTkFrame):
    """
    Entry custom pour la saisie arabe avec support RTL natif Windows.

    Utilise tk.Text mono-ligne + configuration RTL Windows via API ctypes.
    Résout le problème de copier-coller arabe inversé.
    """

    def __init__(
        self,
        master,
        width: Optional[int] = None,
        height: int = 40,
        font=None,
        fg_color: str = "#F8FAFC",
        border_color: str = "#E2E8F0",
        text_color: str = "#1E293B",
        placeholder_text: str = "",
        corner_radius: int = 8,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=fg_color,
            corner_radius=corner_radius,
            border_width=1,
            border_color=border_color,
            height=height,
            **kwargs
        )

        self._placeholder_text = placeholder_text
        self._placeholder_shown = False
        self._text_color = text_color
        self._placeholder_color = "#94A3B8"

        self._text_widget = tk.Text(
            self,
            height=1,
            wrap="none",
            font=font or ("Segoe UI", 13),
            bg=fg_color,
            fg=text_color,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            insertbackground=text_color,
            padx=12,
            pady=(height - 24) // 2,
            selectbackground="#3B82F6",
            selectforeground="#FFFFFF",
        )
        self._text_widget.pack(fill="both", expand=True, padx=1, pady=1)

        # Configure RTL natif Windows (résout le copier-coller arabe)
        self.after(100, lambda: set_windows_rtl(self._text_widget))

        # Comportement Entry-like
        self._text_widget.bind("<Return>", lambda e: self._on_return())
        self._text_widget.bind("<Tab>", lambda e: self._on_tab())
        self._text_widget.bind("<FocusIn>", lambda e: self._on_focus_in())
        self._text_widget.bind("<FocusOut>", lambda e: self._on_focus_out())
        self._text_widget.bind("<KeyRelease>", lambda e: self._on_key_release())

        # Intercepte le collage pour gérer le BIDI
        self._text_widget.bind("<<Paste>>", self._on_paste)
        self._text_widget.bind("<Control-v>", self._on_paste)
        self._text_widget.bind("<Control-V>", self._on_paste)

        if placeholder_text:
            self._show_placeholder()

    def _on_paste(self, event=None):
        """Intercepte le collage et corrige le BIDI si nécessaire."""
        try:
            text = self._text_widget.clipboard_get()
        except tk.TclError:
            return "break"

        self._hide_placeholder()

        # Si le texte est arabe, vérifie s'il est déjà en forme visuelle
        if is_arabic(text) and _ARABIC_RESHAPER_AVAILABLE:
            reshaped = reshape_arabic(text)
            if reshaped == text:
                # Déjà en forme visuelle → remet en logique
                text = reverse_for_storage(text)

        # Supprime la sélection et insère
        try:
            self._text_widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

        self._text_widget.insert("insert", text)
        return "break"

    def _show_placeholder(self):
        if not self._text_widget.get("1.0", "end-1c"):
            self._text_widget.insert("1.0", self._placeholder_text)
            self._text_widget.config(fg=self._placeholder_color)
            self._placeholder_shown = True

    def _hide_placeholder(self):
        if self._placeholder_shown:
            self._text_widget.delete("1.0", "end")
            self._text_widget.config(fg=self._text_color)
            self._placeholder_shown = False

    def _on_focus_in(self):
        self._hide_placeholder()

    def _on_focus_out(self):
        if not self._text_widget.get("1.0", "end-1c").strip():
            self._show_placeholder()

    def _on_key_release(self):
        if self._placeholder_shown:
            self._hide_placeholder()

    def _on_return(self):
        self.event_generate("<<ArabicEntryReturn>>")

    def _on_tab(self):
        self.tk_focusNext().focus()

    def get(self) -> str:
        text = self._text_widget.get("1.0", "end-1c")
        if self._placeholder_shown:
            return ""
        return text.strip()

    def insert(self, index, text: str):
        self._hide_placeholder()
        self._text_widget.delete("1.0", "end")
        self._text_widget.insert("1.0", text)

    def delete(self, first, last=None):
        self._text_widget.delete(first, last)

    def focus(self):
        self._text_widget.focus_set()

    def bind(self, sequence, func, add=None):
        self._text_widget.bind(sequence, func, add)

    @property
    def text_widget(self):
        return self._text_widget


class ArabicCTkTextbox(ctk.CTkTextbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_original(self, index1: str = "0.0", index2: str = "end") -> str:
        return self.get(index1, index2).strip()