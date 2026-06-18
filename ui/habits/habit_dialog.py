"""
ui/habits/habit_dialog.py
Dialog pour créer/éditer une habitude avec support arabe RTL.
"""

from typing import Callable, Optional, Dict
import json

import customtkinter as ctk
import tkinter as tk

from utils.arabic_text import (
    prepare_for_display,
    ArabicCTkLabel,
    ArabicCTkButton,
    ArabicCTkRadioButton,
    ArabicCTkCheckBox,
    ArabicCTkOptionMenu,
)

from database.database import DatabaseManager
from services.habit_service import HabitService
from utils.arabic_keyboard import ArabicKeyboardTextbox


class HabitDialog(ctk.CTkToplevel):
    """Dialog création/édition d'habitude avec support arabe."""

    def __init__(
        self,
        master,
        db: DatabaseManager,
        goal_service=None,
        habit_id: Optional[int] = None,
        on_save: Optional[Callable] = None
    ):
        super().__init__(master)
        self.goal_service = goal_service
        self.service = HabitService(db)
        self.habit_id = habit_id
        self.on_save = on_save
        self.result = None

        title = "✏️ Modifier l'habitude" if habit_id else "✏️ Nouvelle habitude"
        self.title(prepare_for_display(title))
        self.geometry("420x520")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        self._center_on_master(master)
        self._build_ui()

        if habit_id:
            self._load_habit()

    def _center_on_master(self, master) -> None:
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 420) // 2
        y = master.winfo_y() + (master.winfo_height() - 520) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="#FFFFFF", corner_radius=0,
            scrollbar_fg_color="#E2E8F0",
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color="#94A3B8"
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        content = ctk.CTkFrame(scroll, fg_color="#FFFFFF")
        content.pack(fill="x", expand=True)

        # Titre
        ArabicCTkLabel(
            content, text=prepare_for_display("✨ Nouvelle habitude"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # ═══════════════════════════════════════════════════
        # NOM — ArabicKeyboardTextbox (single line)
        # ═══════════════════════════════════════════════════
        ArabicCTkLabel(
            content, text=prepare_for_display("Nom:"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(10, 5))

        self.name_entry = ArabicKeyboardTextbox(
            content,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#F8FAFC",
            border_color="#E2E8F0",
            text_color="#1E293B",
            placeholder_text="Nom de l'habitude..."
        )
        self.name_entry.pack(fill="x", padx=20, pady=5)

        # ═══════════════════════════════════════════════════
        # DESCRIPTION — ArabicKeyboardTextbox (multi-lignes)
        # ═══════════════════════════════════════════════════
        ArabicCTkLabel(
            content, text=prepare_for_display("Description (optionnel):"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(10, 5))

        self.desc_entry = ArabicKeyboardTextbox(
            content,
            height=80,
            font=ctk.CTkFont(size=13),
            fg_color="#F8FAFC",
            border_color="#E2E8F0",
            text_color="#1E293B",
            placeholder_text="Description"
        )
        self.desc_entry.pack(fill="x", padx=20, pady=5)

        # Fréquence
        ArabicCTkLabel(
            content, text=prepare_for_display("Fréquence:"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(10, 5))
        self.freq_var = ctk.StringVar(value="daily")
        freq_frame = ctk.CTkFrame(content, fg_color="transparent")
        freq_frame.pack(fill="x", padx=20, pady=5)

        for val, label in [
            ("daily", "Tous les jours"),
            ("weekly", "Cible hebdo"),
            ("custom", "Jours spécifiques")
        ]:
            ArabicCTkRadioButton(
                freq_frame, text=prepare_for_display(label), variable=self.freq_var, value=val,
                font=ctk.CTkFont(size=11), text_color="#475569"
            ).pack(side="left", padx=10)

        # Jours spécifiques (visible si custom)
        self.days_frame = ctk.CTkFrame(content, fg_color="#F8FAFC", corner_radius=8)
        self.days_frame.pack(fill="x", padx=20, pady=5)
        self.days_vars = {}
        days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for i, day in enumerate(days):
            var = ctk.BooleanVar()
            self.days_vars[i] = var
            ArabicCTkCheckBox(
                self.days_frame, text=prepare_for_display(day), variable=var,
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=8, pady=8)

        # Couleur
        ArabicCTkLabel(
            content, text=prepare_for_display("Couleur:"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(10, 5))
        self.color_var = ctk.StringVar(value="#3B82F6")
        colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#059669"]
        color_frame = ctk.CTkFrame(content, fg_color="transparent")
        color_frame.pack(fill="x", padx=20, pady=5)

        for c in colors:
            btn = ctk.CTkButton(
                color_frame, text="", width=28, height=28, corner_radius=14,
                fg_color=c, hover_color=c,
                command=lambda col=c: self.color_var.set(col)
            )
            btn.pack(side="left", padx=4)

        # Icône
        ArabicCTkLabel(
            content, text=prepare_for_display("Icône:"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(10, 5))
        self.icon_var = ctk.StringVar(value="✨")
        icons = ["✨", "🏃", "📖", "🕌", "💧", "🧘", "💪", "🥗", "💤", "🎯"]
        icon_frame = ctk.CTkFrame(content, fg_color="transparent")
        icon_frame.pack(fill="x", padx=20, pady=5)

        for ic in icons:
            btn = ctk.CTkButton(
                icon_frame, text=ic, width=32, height=32, corner_radius=6,
                fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#1E293B",
                font=ctk.CTkFont(size=16),
                command=lambda i=ic: self.icon_var.set(i)
            )
            btn.pack(side="left", padx=2)

        # ═══════════════════════════════════════════════════
        # LIEN GOAL / TÂCHE
        # ═══════════════════════════════════════════════════
        ArabicCTkLabel(
            content, text=prepare_for_display("Lié à un objectif (optionnel):"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(15, 5))

        link_frame = ctk.CTkFrame(content, fg_color="#F8FAFC", corner_radius=8)
        link_frame.pack(fill="x", padx=20, pady=5)

        # Goal
        goal_row = ctk.CTkFrame(link_frame, fg_color="transparent")
        goal_row.pack(fill="x", padx=12, pady=(8, 4))

        ArabicCTkLabel(
            goal_row, text=prepare_for_display("Goal:"),
            font=ctk.CTkFont(size=11), text_color="#475569", width=50
        ).pack(side="left")

        self._load_goals_data()

        goal_names = [prepare_for_display("Aucun")] + [
            prepare_for_display(name) for name in self._goal_map.keys()
        ]
        self.goal_var = ctk.StringVar(value=prepare_for_display("Aucun"))
        self.goal_menu = ArabicCTkOptionMenu(
            goal_row,
            values=goal_names,
            variable=self.goal_var,
            width=250, height=28,
            fg_color="#FFFFFF", button_color="#E2E8F0", text_color="#1E293B",
            font=ctk.CTkFont(size=11),
            command=self._on_goal_selected
        )
        self.goal_menu.pack(side="left", padx=5)

        # Tâche
        task_row = ctk.CTkFrame(link_frame, fg_color="transparent")
        task_row.pack(fill="x", padx=12, pady=(4, 8))

        ArabicCTkLabel(
            task_row, text=prepare_for_display("Tâche:"),
            font=ctk.CTkFont(size=11), text_color="#475569", width=50
        ).pack(side="left")

        self.task_var = ctk.StringVar(value="")
        self.task_menu = ArabicCTkOptionMenu(
            task_row,
            values=[prepare_for_display("Aucune")],
            variable=self.task_var,
            width=250, height=28,
            fg_color="#FFFFFF", button_color="#E2E8F0", text_color="#1E293B",
            font=ctk.CTkFont(size=11),
            state="disabled"
        )
        self.task_menu.pack(side="left", padx=5)

        # Boutons
        ctk.CTkFrame(content, height=1, fg_color="#E2E8F0").pack(fill="x", padx=20, pady=15)

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 20))

        ArabicCTkButton(
            btn_frame, text=prepare_for_display("Annuler"), width=90,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        ).pack(side="left", padx=5)

        ArabicCTkButton(
            btn_frame, text=prepare_for_display("💾 Sauvegarder"), width=120,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_save
        ).pack(side="right", padx=5)

    def _load_habit(self) -> None:
        """Charge les données si édition."""
        habit = self.service.get_habit(self.habit_id)
        if not habit:
            return

        # CORRECTION : Utiliser set_value() pour les deux (même API)
        self.name_entry.set_value(habit.get("title", ""))
        self.desc_entry.set_value(habit.get("description", ""))

        self.freq_var.set(habit.get("frequency", "daily"))
        self.color_var.set(habit.get("color", "#3B82F6"))
        if habit.get("icon"):
            self.icon_var.set(habit["icon"])

        # Jours spécifiques
        if habit.get("target_days"):
            try:
                days = json.loads(habit["target_days"])
                for i in days:
                    if i in self.days_vars:
                        self.days_vars[i].set(True)
            except (json.JSONDecodeError, TypeError):
                pass

        # Goal / Task
        if habit.get("goal_id") and self.goal_service:
            goal = self.goal_service.get_goal(habit["goal_id"])
            if goal:
                display_title = prepare_for_display(goal.title)
                self.goal_var.set(display_title)
                self._on_goal_selected(goal.title)

                if habit.get("task_id"):
                    tasks = self._tasks_by_goal.get(goal.id, [])
                    for tid, tname in tasks:
                        if tid == habit["task_id"]:
                            self.task_var.set(prepare_for_display(tname))
                            break

    def _on_save(self) -> None:
        # CORRECTION : .get() sans arguments pour ArabicKeyboardTextbox
        title = self.name_entry.get().strip()
        if not title:
            return

        desc = self.desc_entry.get().strip()
        freq = self.freq_var.get()

        target_days = None
        if freq == "custom":
            days = [i for i, var in self.days_vars.items() if var.get()]
            target_days = json.dumps(days)

        # Récupérer goal_id et task_id
        goal_display = self.goal_var.get()
        goal_id = None
        for orig_name, gid in self._goal_map.items():
            if prepare_for_display(orig_name) == goal_display:
                goal_id = gid
                break

        task_display = self.task_var.get()
        task_id = None
        for orig_name, tid in self._task_map.items():
            if prepare_for_display(orig_name) == task_display:
                task_id = tid
                break

        if self.habit_id:
            self.service.update_habit(
                self.habit_id, title=title, description=desc or None,
                goal_id=goal_id, task_id=task_id,
                frequency=freq, target_days=target_days,
                color=self.color_var.get(), icon=self.icon_var.get()
            )
        else:
            self.service.create_habit(
                title=title, description=desc or None,
                goal_id=goal_id, task_id=task_id,
                frequency=freq, target_days=target_days,
                color=self.color_var.get(), icon=self.icon_var.get()
            )

        if self.on_save:
            self.on_save()

        self.destroy()

    def _load_goals_data(self) -> None:
        """Charge goals et tâches depuis la DB."""
        self._goal_map: Dict[str, int] = {}
        self._task_map: Dict[str, int] = {}
        self._tasks_by_goal: Dict[int, list] = {}

        if not self.goal_service:
            return

        goals = self.goal_service.list_goals()
        for goal in goals:
            self._goal_map[goal.title] = goal.id

            tasks = self.goal_service.db.get_tasks_by_goal_id(goal.id)
            self._tasks_by_goal[goal.id] = [
                (t["id"], t["name"]) for t in tasks
            ]

    def _on_goal_selected(self, goal_name: str) -> None:
        """Quand un goal est sélectionné, charge ses tâches."""
        if goal_name == "Aucun" or goal_name not in self._goal_map:
            self.task_menu.set_values([prepare_for_display("Aucune")])
            self.task_menu.configure(state="disabled")
            self.task_var.set(prepare_for_display("Aucune"))
            self._task_map = {}
            return

        goal_id = self._goal_map[goal_name]
        tasks = self._tasks_by_goal.get(goal_id, [])

        self._task_map = {name: tid for tid, name in tasks}
        task_names = [prepare_for_display("Aucune")] + [
            prepare_for_display(name) for name in self._task_map.keys()
        ]

        self.task_menu.set_values(task_names)
        self.task_menu.configure(state="normal")
        self.task_var.set(prepare_for_display("Aucune"))