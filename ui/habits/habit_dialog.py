"""
ui/habits/habit_dialog.py
Dialog pour créer/éditer une habitude.
"""

from typing import Callable, Optional, Dict

import customtkinter as ctk

from database.database import DatabaseManager
from services.habit_service import HabitService


class HabitDialog(ctk.CTkToplevel):
    """Dialog création/édition d'habitude."""

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

        self.title("✏️ Nouvelle habitude" if not habit_id else "✏️ Modifier l'habitude")
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
        ctk.CTkLabel(
            content, text="✨ Nouvelle habitude",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Nom
        ctk.CTkLabel(content, text="Nom:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(padx=20, anchor="w", pady=(10, 5))
        self.name_entry = ctk.CTkEntry(
            content, height=40, corner_radius=8,
            border_width=1, border_color="#E2E8F0",
            fg_color="#F8FAFC", text_color="#1E293B",
            font=ctk.CTkFont(size=13)
        )
        self.name_entry.pack(fill="x", padx=20, pady=5)

        # Description
        ctk.CTkLabel(content, text="Description (optionnel):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(padx=20, anchor="w", pady=(10, 5))
        self.desc_entry = ctk.CTkTextbox(
            content, height=60, wrap="word",
            corner_radius=8, border_width=1, border_color="#E2E8F0",
            fg_color="#F8FAFC", text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.desc_entry.pack(fill="x", padx=20, pady=5)

        # Fréquence
        ctk.CTkLabel(content, text="Fréquence:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(padx=20, anchor="w", pady=(10, 5))
        self.freq_var = ctk.StringVar(value="daily")
        freq_frame = ctk.CTkFrame(content, fg_color="transparent")
        freq_frame.pack(fill="x", padx=20, pady=5)

        for val, label in [("daily", "Tous les jours"), ("weekly", "Cible hebdo"), ("custom", "Jours spécifiques")]:
            ctk.CTkRadioButton(
                freq_frame, text=label, variable=self.freq_var, value=val,
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
            ctk.CTkCheckBox(
                self.days_frame, text=day, variable=var,
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=8, pady=8)

        # Couleur
        ctk.CTkLabel(content, text="Couleur:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(padx=20, anchor="w", pady=(10, 5))
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
        ctk.CTkLabel(content, text="Icône:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(padx=20, anchor="w", pady=(10, 5))
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
        ctk.CTkLabel(
            content, text="Lié à un objectif (optionnel):",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569"
        ).pack(padx=20, anchor="w", pady=(15, 5))

        link_frame = ctk.CTkFrame(content, fg_color="#F8FAFC", corner_radius=8)
        link_frame.pack(fill="x", padx=20, pady=5)

        # Goal
        goal_row = ctk.CTkFrame(link_frame, fg_color="transparent")
        goal_row.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(goal_row, text="Goal:", font=ctk.CTkFont(size=11), text_color="#475569", width=50).pack(side="left")

        self._load_goals_data()

        goal_names = ["Aucun"] + list(self._goal_map.keys())
        self.goal_var = ctk.StringVar(value="Aucun")
        self.goal_menu = ctk.CTkOptionMenu(
            goal_row,
            values=goal_names,
            variable=self.goal_var,
            width=250, height=28,
            fg_color="#FFFFFF", button_color="#E2E8F0", text_color="#1E293B",
            font=ctk.CTkFont(size=11),
            command=self._on_goal_selected
        )
        self.goal_menu.pack(side="left", padx=5)

        # Tâche (désactivée tant qu'aucun goal n'est sélectionné)
        task_row = ctk.CTkFrame(link_frame, fg_color="transparent")
        task_row.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkLabel(task_row, text="Tâche:", font=ctk.CTkFont(size=11), text_color="#475569", width=50).pack(side="left")

        self.task_var = ctk.StringVar(value="")
        self.task_menu = ctk.CTkOptionMenu(
            task_row,
            values=["Aucune"],
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

        ctk.CTkButton(
            btn_frame, text="Annuler", width=90,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="💾 Sauvegarder", width=120,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_save
        ).pack(side="right", padx=5)

    def _load_habit(self) -> None:
        """Charge les données si édition."""
        habit = self.service.get_habit(self.habit_id)
        if not habit:
            return

        self.name_entry.insert(0, habit["title"])
        if habit.get("description"):
            self.desc_entry.insert("0.0", habit["description"])
        self.freq_var.set(habit.get("frequency", "daily"))
        self.color_var.set(habit.get("color", "#3B82F6"))
        if habit.get("icon"):
            self.icon_var.set(habit["icon"])

        # Goal / Task
        if habit.get("goal_id") and self.goal_service:
            goal = self.goal_service.get_goal(habit["goal_id"])
            if goal:
                self.goal_var.set(goal.title)
                self._on_goal_selected(goal.title)

                if habit.get("task_id"):
                    # Trouver le nom de la tâche
                    tasks = self._tasks_by_goal.get(goal.id, [])
                    for tid, tname in tasks:
                        if tid == habit["task_id"]:
                            self.task_var.set(tname)
                            break

    def _on_save(self) -> None:
        title = self.name_entry.get().strip()
        if not title:
            return

        desc = self.desc_entry.get("0.0", "end").strip()
        freq = self.freq_var.get()

        target_days = None
        if freq == "custom":
            days = [i for i, var in self.days_vars.items() if var.get()]
            import json
            target_days = json.dumps(days)

        # Récupérer goal_id et task_id
        goal_name = self.goal_var.get()
        goal_id = self._goal_map.get(goal_name) if goal_name != "Aucun" else None

        task_name = self.task_var.get()
        task_id = self._task_map.get(task_name) if task_name != "Aucune" else None

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

            # Récupérer les tâches de ce goal via la DB directement
            # ou via le service si la méthode existe
            tasks = self.goal_service.db.get_tasks_by_goal_id(goal.id)
            self._tasks_by_goal[goal.id] = [
                (t["id"], t["name"]) for t in tasks
            ]

    def _on_goal_selected(self, goal_name: str) -> None:
        """Quand un goal est sélectionné, charge ses tâches."""
        if goal_name == "Aucun" or goal_name not in self._goal_map:
            self.task_menu.configure(values=["Aucune"], state="disabled")
            self.task_var.set("Aucune")
            self._task_map = {}
            return

        goal_id = self._goal_map[goal_name]
        tasks = self._tasks_by_goal.get(goal_id, [])

        self._task_map = {name: tid for tid, name in tasks}
        task_names = ["Aucune"] + list(self._task_map.keys())

        self.task_menu.configure(values=task_names, state="normal")
        self.task_var.set("Aucune")