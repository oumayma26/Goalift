"""
utils/arabic_keyboard.py
Clavier virtuel arabe pour customtkinter.
Supporte aussi la saisie au clavier physique.
"""

import customtkinter as ctk
from utils.arabic_text import ArabicCTkLabel, prepare_for_display


class ArabicKeyboard(ctk.CTkFrame):
    """
    Clavier virtuel arabe.
    L'utilisateur clique sur les lettres, le texte est construit
    dans le bon ordre RTL (de droite a gauche).
    La previsualisation utilise ArabicCTkLabel (reshape + BIDI correct).
    """

    ROWS = [
        ["ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د"],
        ["ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط"],
        ["ئ", "ء", "ؤ", "ر", "ى", "ة", "و", "ز", "ظ", "ذ"],
    ]

    def __init__(self, master, target_widget, on_close=None, **kwargs):
        super().__init__(master, fg_color="#FFFFFF", corner_radius=12, **kwargs)

        self.target_widget = target_widget
        self.on_close = on_close
        self._text = ""

        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Clavier arabe",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="X",
            width=30,
            height=30,
            corner_radius=6,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._close
        ).pack(side="right")

        # Previsualisation
        preview_frame = ctk.CTkFrame(
            self, fg_color="#F8FAFC", corner_radius=6,
            height=40, border_width=1, border_color="#E2E8F0"
        )
        preview_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        preview_frame.grid_propagate(False)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.preview = ArabicCTkLabel(
            preview_frame,
            text="",
            font=ctk.CTkFont(size=16),
            text_color="#1E293B",
            fg_color="transparent",
            height=40
        )
        self.preview.grid(row=0, column=0, sticky="e", padx=10)

        # Clavier
        keyboard_frame = ctk.CTkFrame(self, fg_color="transparent")
        keyboard_frame.grid(row=2, column=0, padx=10, pady=5)

        for row in self.ROWS:
            row_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
            row_frame.pack(pady=2)

            for letter in row:
                btn = ctk.CTkButton(
                    row_frame,
                    text=letter,
                    width=36,
                    height=36,
                    corner_radius=6,
                    fg_color="#F1F5F9",
                    hover_color="#E2E8F0",
                    text_color="#1E293B",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    command=lambda l=letter: self._on_key(l)
                )
                btn.pack(side="left", padx=2)

        # Touches speciales
        special_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
        special_frame.pack(pady=2)

        ctk.CTkButton(
            special_frame,
            text="<-",
            width=50,
            height=36,
            corner_radius=6,
            fg_color="#FEE2E2",
            hover_color="#FECACA",
            text_color="#EF4444",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_backspace
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            special_frame,
            text="space",
            width=80,
            height=36,
            corner_radius=6,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=14),
            command=lambda: self._on_key(" ")
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            special_frame,
            text="Valider",
            width=80,
            height=36,
            corner_radius=6,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_validate
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            special_frame,
            text="Effacer",
            width=70,
            height=36,
            corner_radius=6,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12),
            command=self._on_clear
        ).pack(side="left", padx=2)

    def _on_key(self, letter):
        self._text += letter
        self._update_preview()

    def _on_backspace(self):
        self._text = self._text[:-1]
        self._update_preview()

    def _on_clear(self):
        self._text = ""
        self._update_preview()

    def _update_preview(self):
        self.preview.set_text(self._text)

    def _on_validate(self):
        if self.target_widget:
            if hasattr(self.target_widget, "set_value"):
                self.target_widget.set_value(self._text)
            elif hasattr(self.target_widget, "delete") and hasattr(self.target_widget, "insert"):
                self.target_widget.delete(0, "end")
                self.target_widget.insert(0, self._text)
        self._close()

    def _close(self):
        if self.on_close:
            self.on_close()
        self.destroy()


class ArabicKeyboardEntry(ctk.CTkFrame):
    """
    Entry avec bouton clavier arabe integre.
    Affiche le texte arabe correctement via ArabicCTkLabel.
    Stocke la valeur brute pour la DB.
    Supporte la saisie au clavier physique ET virtuel.
    """

    def __init__(
        self,
        master,
        height=40,
        font=None,
        fg_color="#F8FAFC",
        border_color="#E2E8F0",
        text_color="#1E293B",
        placeholder_text="",
        corner_radius=8,
        **kwargs
    ):
        frame_kwargs = {
            "fg_color": fg_color,
            "corner_radius": corner_radius,
            "border_width": 1,
            "border_color": border_color,
            "height": height,
        }
        frame_kwargs.update(kwargs)
        super().__init__(master, **frame_kwargs)

        self._stored_value = ""
        self._placeholder_text = placeholder_text
        self._placeholder_shown = True
        self._text_color = text_color
        self._border_color = border_color
        self._is_focused = False
        self._frame_fg = fg_color

        # ENTRY INVISIBLE — capture le clavier physique
        self._entry_var = ctk.StringVar()
        self._hidden_entry = ctk.CTkEntry(
            self,
            textvariable=self._entry_var,
            fg_color=fg_color,
            border_width=0,
            text_color=fg_color,
            width=1,
            height=1,
            font=ctk.CTkFont(size=1)
        )
        self._hidden_entry.place(x=-100, y=-100)

        self._entry_var.trace_add("write", self._on_entry_changed)

        self.bind("<Button-1>", self._on_click)
        self._hidden_entry.bind("<FocusIn>", self._on_focus_in)
        self._hidden_entry.bind("<FocusOut>", self._on_focus_out)
        self._hidden_entry.bind("<KeyRelease>", self._on_key_release)

        self.display_label = ArabicCTkLabel(
            self,
            text=placeholder_text,
            font=font or ctk.CTkFont(size=13),
            text_color="#94A3B8" if placeholder_text else text_color,
            fg_color=fg_color,
            height=height - 2
        )
        self.display_label.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=1)
        self.display_label.bind("<Button-1>", self._on_click)

        self.kb_btn = ctk.CTkButton(
            self,
            text="AR",
            width=36,
            height=height - 8,
            corner_radius=6,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_keyboard
        )
        self.kb_btn.pack(side="right", padx=(5, 5), pady=1)

        self._keyboard_window = None

    def _on_click(self, event=None):
        self._hidden_entry.focus_set()

    def _on_focus_in(self, event=None):
        self._is_focused = True
        self._update_border_color()

    def _on_focus_out(self, event=None):
        self._is_focused = False
        self._update_border_color()

    def _update_border_color(self):
        color = "#3B82F6" if self._is_focused else self._border_color
        super().configure(border_color=color)

    def _on_entry_changed(self, *args):
        self._stored_value = self._entry_var.get()
        self._update_display()

    def _on_key_release(self, event):
        if event.keysym == "Delete":
            self._stored_value = ""
            self._entry_var.set("")
            self._update_display()

    def _update_display(self):
        if self._stored_value:
            self.display_label.set_text(self._stored_value)
            self.display_label.configure(text_color=self._text_color)
            self._placeholder_shown = False
        elif self._placeholder_text:
            self.display_label.set_text(self._placeholder_text)
            self.display_label.configure(text_color="#94A3B8")
            self._placeholder_shown = True
        else:
            self.display_label.set_text("")
            self._placeholder_shown = False

    def set_value(self, text):
        self._stored_value = text
        self._entry_var.set(text)
        self._update_display()

    def get(self, *args):
        if len(args) == 0:
            return self._stored_value
        elif len(args) == 2 and args[0] == "0.0" and args[1] == "end":
            return self._stored_value
        else:
            raise TypeError(
                f"ArabicKeyboardEntry.get() takes 0 or 2 arguments ({len(args)} given)"
            )

    def insert(self, index, text):
        self._stored_value = text
        self._entry_var.set(text)
        self._update_display()

    def delete(self, first=None, last=None):
        self._stored_value = ""
        self._entry_var.set("")
        self._update_display()

    def configure(self, **kwargs):
        if "placeholder_text" in kwargs:
            self._placeholder_text = kwargs.pop("placeholder_text")
            self._update_display()
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            if not self._is_focused:
                self._update_border_color()
        if "fg_color" in kwargs:
            self._frame_fg = kwargs.pop("fg_color")
            self.display_label.configure(fg_color=self._frame_fg)
            self._hidden_entry.configure(fg_color=self._frame_fg)
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            if not self._placeholder_shown:
                self.display_label.configure(text_color=self._text_color)
        if kwargs:
            super().configure(**kwargs)

    def _open_keyboard(self):
        if self._keyboard_window and self._keyboard_window.winfo_exists():
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Clavier arabe")
        popup.geometry("500x320")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        popup.update_idletasks()
        x = popup.winfo_screenwidth() // 2 - 250
        y = popup.winfo_screenheight() // 2 - 160
        popup.geometry(f"+{x}+{y}")

        keyboard = ArabicKeyboard(
            popup,
            target_widget=self,
            on_close=lambda: popup.destroy()
        )
        keyboard.pack(fill="both", expand=True, padx=10, pady=10)

        self._keyboard_window = popup


# ═══════════════════════════════════════════════════════════════════
# NOUVEAU : ArabicKeyboardTextbox — Multi-lignes avec clavier arabe
# ═══════════════════════════════════════════════════════════════════

class ArabicKeyboardTextbox(ctk.CTkFrame):
    """
    Textbox multi-lignes avec bouton clavier arabe integre.
    Wrap un CTkTextbox reel pour le support multi-lignes,
    mais avec un bouton AR pour le clavier virtuel.
    """

    def __init__(
        self,
        master,
        height=80,
        font=None,
        fg_color="#F8FAFC",
        border_color="#E2E8F0",
        text_color="#1E293B",
        placeholder_text="",
        corner_radius=8,
        **kwargs
    ):
        frame_kwargs = {
            "fg_color": fg_color,
            "corner_radius": corner_radius,
            "border_width": 1,
            "border_color": border_color,
            "height": height,
        }
        frame_kwargs.update(kwargs)
        super().__init__(master, **frame_kwargs)

        self._text_color = text_color
        self._border_color = border_color
        self._is_focused = False
        self._frame_fg = fg_color

        # CTkTextbox reel (multi-lignes)
        self.textbox = ctk.CTkTextbox(
            self,
            height=height - 2,
            font=font or ctk.CTkFont(size=13),
            fg_color=fg_color,
            text_color=text_color,
            border_width=0,
            corner_radius=corner_radius - 2,
            wrap="word",
            activate_scrollbars=True
        )
        self.textbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=1)

        # Placeholder handling
        self._placeholder_text = placeholder_text
        self._placeholder_shown = False
        if placeholder_text:
            self.textbox.insert("0.0", placeholder_text)
            self.textbox.configure(text_color="#94A3B8")
            self._placeholder_shown = True

        # Bind pour placeholder
        self.textbox.bind("<FocusIn>", self._on_focus_in)
        self.textbox.bind("<FocusOut>", self._on_focus_out)

        # Bouton clavier arabe
        self.kb_btn = ctk.CTkButton(
            self,
            text="AR",
            width=36,
            height=28,
            corner_radius=6,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_keyboard
        )
        self.kb_btn.pack(side="right", padx=(5, 5), pady=1)

        self._keyboard_window = None

    def _on_focus_in(self, event=None):
        self._is_focused = True
        if self._placeholder_shown:
            self.textbox.delete("0.0", "end")
            self.textbox.configure(text_color=self._text_color)
            self._placeholder_shown = False
        super().configure(border_color="#3B82F6")

    def _on_focus_out(self, event=None):
        self._is_focused = False
        content = self.textbox.get("0.0", "end").strip()
        if not content and self._placeholder_text:
            self.textbox.delete("0.0", "end")
            self.textbox.insert("0.0", self._placeholder_text)
            self.textbox.configure(text_color="#94A3B8")
            self._placeholder_shown = True
        super().configure(border_color=self._border_color)

    # ─── API publique — identique à CTkTextbox ───

    def get(self, start="0.0", end="end"):
        """Retourne le texte brut."""
        if self._placeholder_shown:
            return ""
        return self.textbox.get(start, end).strip()

    def insert(self, index, text):
        """Insert du texte a l'index donne."""
        if self._placeholder_shown:
            self.textbox.delete("0.0", "end")
            self.textbox.configure(text_color=self._text_color)
            self._placeholder_shown = False
        self.textbox.insert(index, text)

    def delete(self, start, end=None):
        """Supprime le texte entre start et end."""
        self.textbox.delete(start, end if end else start)

    def set_value(self, text):
        """Remplace tout le contenu."""
        self.textbox.delete("0.0", "end")
        if text:
            self.textbox.insert("0.0", text)
            self.textbox.configure(text_color=self._text_color)
            self._placeholder_shown = False
        elif self._placeholder_text:
            self.textbox.insert("0.0", self._placeholder_text)
            self.textbox.configure(text_color="#94A3B8")
            self._placeholder_shown = True

    def configure(self, **kwargs):
        if "placeholder_text" in kwargs:
            self._placeholder_text = kwargs.pop("placeholder_text")
            if not self.textbox.get("0.0", "end").strip():
                self.set_value("")
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            if not self._is_focused:
                super().configure(border_color=self._border_color)
        if "fg_color" in kwargs:
            self._frame_fg = kwargs.pop("fg_color")
            self.textbox.configure(fg_color=self._frame_fg)
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            if not self._placeholder_shown:
                self.textbox.configure(text_color=self._text_color)
        if kwargs:
            super().configure(**kwargs)

    def _open_keyboard(self):
        """Ouvre le clavier virtuel arabe."""
        if self._keyboard_window and self._keyboard_window.winfo_exists():
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Clavier arabe")
        popup.geometry("500x320")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        popup.update_idletasks()
        x = popup.winfo_screenwidth() // 2 - 250
        y = popup.winfo_screenheight() // 2 - 160
        popup.geometry(f"+{x}+{y}")

        # Creer un wrapper pour que le clavier puisse injecter du texte
        class TextboxWrapper:
            def __init__(self, textbox):
                self.textbox = textbox

            def set_value(self, text):
                self.textbox.delete("0.0", "end")
                self.textbox.insert("0.0", text)
                self.textbox.configure(text_color="#1E293B")

            def delete(self, first, last=None):
                self.textbox.delete("0.0", "end")

            def insert(self, index, text):
                self.textbox.delete("0.0", "end")
                self.textbox.insert("0.0", text)

        wrapper = TextboxWrapper(self.textbox)

        keyboard = ArabicKeyboard(
            popup,
            target_widget=wrapper,
            on_close=lambda: popup.destroy()
        )
        keyboard.pack(fill="both", expand=True, padx=10, pady=10)

        self._keyboard_window = popup