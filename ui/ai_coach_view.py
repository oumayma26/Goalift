"""
ui/ai_coach_view.py
Vue du coach IA — interface chat avec Ollama.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
from threading import Thread

from services.ai_coach import AICoachService, ChatMessage
from utils.arabic_text import prepare_for_display, ArabicCTkLabel


class ChatBubble(ctk.CTkFrame):
    """Bulle de message dans le chat."""

    COLORS = {
        "user": {"bg": "#3B82F6", "text": "#FFFFFF"},
        "assistant": {"bg": "#F1F5F9", "text": "#1E293B"},
        "system": {"bg": "#FEF3C7", "text": "#92400E"},
    }

    def __init__(self, master, message: ChatMessage, **kwargs):
        is_user = message.role == "user"
        colors = self.COLORS.get(message.role, self.COLORS["assistant"])

        super().__init__(
            master,
            fg_color=colors["bg"],
            corner_radius=12,
            **kwargs
        )

        # Alignement
        self.grid_columnconfigure(0, weight=1 if is_user else 0)
        self.grid_columnconfigure(1, weight=0 if is_user else 1)

        # Label du message
        self.msg_label = ArabicCTkLabel(
            self,
            text=prepare_for_display(message.content),
            font=ctk.CTkFont(size=12),
            text_color=colors["text"],
            fg_color="transparent",
            wraplength=500,
            justify="left" if not is_user else "right"
        )
        self.msg_label.grid(row=0, column=0 if not is_user else 1, sticky="w" if not is_user else "e", padx=12, pady=8)

        # Heure
        time_str = message.timestamp.strftime("%H:%M")
        ctk.CTkLabel(
            self,
            text=time_str,
            font=ctk.CTkFont(size=9),
            text_color=colors["text"],
            fg_color="transparent"
        ).grid(row=1, column=0 if not is_user else 1, sticky="w" if not is_user else "e", padx=12, pady=(0, 4))


class AICoachView(ctk.CTkFrame):
    """
    Vue principale du coach IA.
    Onglet avec interface chat + suggestions rapides.
    """

    QUICK_PROMPTS = [
        "🎯 Aide-moi à définir un objectif SMART",
        "📋 Décompose mon objectif en tâches",
        "💡 Je manque de motivation",
        "🔍 Analyse mes progrès",
        "🧘 Suggère une routine matinale",
    ]

    def __init__(self, master, db_manager=None, **kwargs):
        super().__init__(master, fg_color="#F8FAFC", **kwargs)

        self.db = db_manager
        self.service = AICoachService()
        self._is_generating = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_chat_area()
        self._build_input_area()
        self._build_sidebar()

        # Message de bienvenue
        self._add_system_message(
            "👋 Salut ! Je suis ton coach GoalCoach.\n\n"
            "Je peux t'aider à :\n"
            "• Définir des objectifs SMART\n"
            "• Créer des plans d'action\n"
            "• Rester motivé\n"
            "• Analyser tes progrès\n\n"
            "Pose-moi une question ou choisis une suggestion !"
        )

        # Vérifie Ollama
        self._check_ollama()

    def _build_header(self):
        """Barre d'en-tête avec titre et statut."""
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", height=60, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="🤖 Coach IA",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left", padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            header,
            text="⏳ Vérification d'Ollama...",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.status_label.pack(side="right", padx=20)

        # Bouton nouvelle conversation
        ctk.CTkButton(
            header,
            text="🗑️ Nouvelle conversation",
            width=150,
            height=32,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=11),
            command=self._clear_chat
        ).pack(side="right", padx=10)

    def _build_chat_area(self):
        """Zone de scroll pour les messages."""
        self.chat_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#F8FAFC",
            corner_radius=0,
            scrollbar_fg_color="#E2E8F0",
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color="#94A3B8"
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)

    def _build_input_area(self):
        """Zone de saisie en bas."""
        input_container = ctk.CTkFrame(self, fg_color="#FFFFFF", height=80, corner_radius=0)
        input_container.grid(row=2, column=0, columnspan=2, sticky="ew")
        input_container.grid_propagate(False)
        input_container.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Écris ton message...",
            height=44,
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=13)
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(20, 10), pady=18)
        self.input_entry.bind("<Return>", lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(
            input_container,
            text="➤",
            width=44,
            height=44,
            corner_radius=12,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._send_message
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 20), pady=18)

    def _build_sidebar(self):
        """Barre latérale avec suggestions rapides."""
        sidebar = ctk.CTkFrame(self, fg_color="#FFFFFF", width=240, corner_radius=0)
        sidebar.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(0, 0), pady=0)
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="💡 Suggestions",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(20, 10), padx=15, anchor="w")

        for prompt in self.QUICK_PROMPTS:
            btn = ctk.CTkButton(
                sidebar,
                text=prepare_for_display(prompt),
                height=36,
                corner_radius=8,
                fg_color="#F1F5F9",
                hover_color="#E2E8F0",
                text_color="#475569",
                font=ctk.CTkFont(size=11),
                anchor="w",
                command=lambda p=prompt: self._send_quick_prompt(p)
            )
            btn.pack(fill="x", padx=15, pady=3)

        # Section modèle
        ctk.CTkLabel(
            sidebar,
            text="🧠 Modèle",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(20, 10), padx=15, anchor="w")

        self.model_label = ctk.CTkLabel(
            sidebar,
            text="llama3.2",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            fg_color="#F8FAFC",
            corner_radius=6,
            width=200,
            height=32
        )
        self.model_label.pack(padx=15, pady=5)

        ctk.CTkLabel(
            sidebar,
            text="💾 100% Offline",
            font=ctk.CTkFont(size=10),
            text_color="#10B981"
        ).pack(padx=15, pady=5)

    def _safe_configure(self, widget, **kwargs):
        """Configure un widget en toute sécurité (vérifie s'il existe encore)."""
        try:
            if widget.winfo_exists():
                widget.configure(**kwargs)
        except Exception:
            pass

    def _check_ollama(self):
        """Vérifie si Ollama est disponible."""
        def check():
            try:
                if self.service.is_available():
                    models = self.service.list_models()
                    if models:
                        self._safe_configure(
                            self.status_label,
                            text=f"✅ Connecté — {models[0]}",
                            text_color="#10B981"
                        )
                        self._safe_configure(self.model_label, text=models[0])
                    else:
                        self._safe_configure(
                            self.status_label,
                            text="⚠️ Aucun modèle trouvé",
                            text_color="#F59E0B"
                        )
                else:
                    self._safe_configure(
                        self.status_label,
                        text="❌ Ollama hors ligne",
                        text_color="#EF4444"
                    )
            except Exception:
                pass  # Widget détruit ou autre erreur

        Thread(target=check, daemon=True).start()

    def _add_message(self, message: ChatMessage):
        """Ajoute une bulle de message au chat."""
        bubble = ChatBubble(self.chat_frame, message)
        bubble.pack(fill="x", pady=4, padx=5)
        self._scroll_to_bottom()

    def _add_system_message(self, text: str):
        """Ajoute un message système (bienvenue, info)."""
        msg = ChatMessage(role="system", content=text)
        self._add_message(msg)

    def _send_message(self):
        """Envoie le message de l'utilisateur."""
        text = self.input_entry.get().strip()
        if not text or self._is_generating:
            return

        self.input_entry.delete(0, "end")

        # Message utilisateur
        user_msg = ChatMessage(role="user", content=text)
        self._add_message(user_msg)

        # Placeholder pour la réponse en cours
        self._is_generating = True
        self.send_btn.configure(state="disabled", text="⏳")

        # Génération en thread séparé
        Thread(target=self._generate_response, args=(text,), daemon=True).start()

    def _generate_response(self, text: str):
        """Génère la réponse IA en streaming."""
        try:
            # Crée une bulle vide pour le streaming
            placeholder_msg = ChatMessage(role="assistant", content="")
            self.after(0, lambda: self._create_streaming_bubble(placeholder_msg))

            full_text = ""
            for chunk in self.service.chat_stream(text):
                full_text += chunk
                self.after(0, lambda t=full_text: self._update_streaming_bubble(t))

        finally:
            self._is_generating = False
            self.after(0, lambda: self._safe_configure(self.send_btn, state="normal", text="➤"))

    def _create_streaming_bubble(self, message: ChatMessage):
        """Crée une bulle vide pour le streaming."""
        self._current_bubble = ChatBubble(self.chat_frame, message)
        self._current_bubble.pack(fill="x", pady=4, padx=5)
        self._scroll_to_bottom()

    def _update_streaming_bubble(self, text: str):
        """Met à jour le texte de la bulle en streaming."""
        if hasattr(self, "_current_bubble") and self._current_bubble.winfo_exists():
            self._current_bubble.msg_label.set_text(prepare_for_display(text))
            self._scroll_to_bottom()

    def _send_quick_prompt(self, prompt: str):
        """Envoie une suggestion rapide."""
        # Enlève l'emoji
        clean = prompt.split(" ", 1)[1] if " " in prompt else prompt
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, clean)
        self._send_message()

    def _clear_chat(self):
        """Réinitialise la conversation."""
        self.service.clear_history()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self._add_system_message("🗑️ Conversation réinitialisée. Comment puis-je t'aider ?")

    def _scroll_to_bottom(self):
        """Scroll vers le dernier message."""
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def generate_smart_goal(self, raw_goal: str, callback: Callable):
        """
        API publique : génère un objectif SMART depuis un autre écran.
        Appelle `callback(result_dict)` quand c'est prêt.
        """
        def _gen():
            result = self.service.generate_smart_goal(raw_goal)
            self.after(0, lambda: callback(result))
        Thread(target=_gen, daemon=True).start()