"""
ui/goal_detail_view.py
Panneau de détails affichant les informations d'un goal,
sa barre de progression et la liste de ses tâches.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable
from models import Goal
from services import GoalService
from .dialogs import GoalDialog, TaskDialog
from ui.dialogs import GoalDialog, TaskDialog


class GoalDetailView(ctk.CTkFrame):
    """
    Vue détaillée d'un goal avec toutes ses tâches et sa progression.
    """

    def __init__(
        self,
        master,
        goal: Goal,
        service: GoalService,
        on_update: Callable,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        
        self.goal = goal
        self.service = service
        self.on_update = on_update

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # La liste des tâches prend l'espace

        self._build_header()
        self._build_progress_section()
        self._build_tasks_section()

    # ───────────────────────────────────────────────
    # En-tête du Goal
    # ───────────────────────────────────────────────

    def _build_header(self) -> None:
        """Construit l'en-tête avec les infos principales du goal."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)

        # Titre et priorité
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            title_row,
            text=self.goal.title,
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        # Badge de priorité
        priority_colors = {"Haute": "#FF6B6B", "Moyenne": "#FFD93D", "Faible": "#6BCB77"}
        ctk.CTkLabel(
            title_row,
            text=f"  {self.goal.priority}  ",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=priority_colors.get(self.goal.priority, "gray"),
            text_color="white",
            corner_radius=12
        ).pack(side="right", padx=5)

        # Description
        if self.goal.description:
            desc = ctk.CTkTextbox(header, height=60, wrap="word", state="normal")
            desc.insert("0.0", self.goal.description)
            desc.configure(state="disabled")
            desc.pack(fill="x", pady=5)

        # Métadonnées
        meta = ctk.CTkFrame(header, fg_color="transparent")
        meta.pack(fill="x")

        ctk.CTkLabel(
            meta,
            text=f"📅 Créé le: {self.goal.created_at.strftime('%d/%m/%Y')}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side="left")

        if self.goal.target_date:
            ctk.CTkLabel(
                meta,
                text=f"🎯 Cible: {self.goal.target_date.strftime('%d/%m/%Y')}",
                font=ctk.CTkFont(size=12),
                text_color="#FF6B6B" if self.goal.is_overdue else "gray"
            ).pack(side="left", padx=20)

        # Boutons d'action
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            actions,
            text="✏️ Modifier",
            command=self._edit_goal,
            width=100
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            actions,
            text="🗑️ Supprimer",
            command=self._delete_goal,
            width=100,
            fg_color="#FF6B6B",
            hover_color="#FF4757"
        ).pack(side="left")

    # ───────────────────────────────────────────────
    # Section Progression
    # ───────────────────────────────────────────────

    def _build_progress_section(self) -> None:
        """Construit la section de progression avec barre visuelle."""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=1, column=0, sticky="ew", pady=10)
        progress_frame.grid_columnconfigure(1, weight=1)

        progress = self.service.get_goal_progress(self.goal.id)

        # Label
        ctk.CTkLabel(
            progress_frame,
            text="📊 Progression",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=10)

        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            corner_radius=10
        )
        self.progress_bar.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(progress["percentage"] / 100)

        # Pourcentage
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"{progress['percentage']:.0f}%",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.progress_label.grid(row=0, column=2, padx=15, pady=10)

        # Compteur de tâches
        ctk.CTkLabel(
            progress_frame,
            text=f"({progress['completed_tasks']}/{progress['total_tasks']} tâches)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 10))

    # ───────────────────────────────────────────────
    # Section Tâches
    # ───────────────────────────────────────────────

    def _build_tasks_section(self) -> None:
        """Construit la section liste des tâches avec actions."""
        tasks_frame = ctk.CTkFrame(self)
        tasks_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        tasks_frame.grid_columnconfigure(0, weight=1)
        tasks_frame.grid_rowconfigure(1, weight=1)

        # En-tête de la section
        tasks_header = ctk.CTkFrame(tasks_frame, fg_color="transparent")
        tasks_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            tasks_header,
            text="✅ Tâches",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            tasks_header,
            text="➕ Ajouter une tâche",
            command=self._add_task,
            width=150
        ).pack(side="right")

        # Liste des tâches
        self.tasks_scroll = ctk.CTkScrollableFrame(tasks_frame, label_text="")
        self.tasks_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self._refresh_tasks_list()

    def _refresh_tasks_list(self) -> None:
        """Recharge la liste des tâches."""
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        tasks = self.service.list_tasks(self.goal.id)

        if not tasks:
            ctk.CTkLabel(
                self.tasks_scroll,
                text="Aucune tâche pour ce goal",
                text_color="gray"
            ).pack(pady=20)
            return

        for task in tasks:
            self._create_task_row(task)

        # Mettre à jour la barre de progression
        progress = self.service.get_goal_progress(self.goal.id)
        self.progress_bar.set(progress["percentage"] / 100)
        self.progress_label.configure(text=f"{progress['percentage']:.0f}%")

    def _create_task_row(self, task) -> None:
        """Crée une ligne de tâche avec actions."""
        row = ctk.CTkFrame(self.tasks_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)

        # Checkbox de statut
        status_var = ctk.StringVar(value="on" if task.is_completed else "off")
        checkbox = ctk.CTkCheckBox(
            row,
            text="",
            variable=status_var,
            onvalue="on",
            offvalue="off",
            width=20,
            command=lambda t=task: self._toggle_task(t)
        )
        checkbox.pack(side="left", padx=(0, 10))
        if task.is_completed:
            checkbox.select()

        # Nom de la tâche (barré si terminée)
        name_color = "gray" if task.is_completed else ("black", "white")
        font = ctk.CTkFont(size=13, overstrike=task.is_completed)
        
        name_label = ctk.CTkLabel(
            row,
            text=task.name,
            font=font,
            text_color=name_color,
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)

        # Boutons d'action
        if not task.is_completed:
            ctk.CTkButton(
                row,
                text="✏️",
                width=30,
                command=lambda t=task: self._edit_task(t)
            ).pack(side="right", padx=2)

        ctk.CTkButton(
            row,
            text="🗑️",
            width=30,
            fg_color="#FF6B6B",
            hover_color="#FF4757",
            command=lambda t=task: self._delete_task(t)
        ).pack(side="right", padx=2)

    # ───────────────────────────────────────────────
    # Actions
    # ───────────────────────────────────────────────

    def _toggle_task(self, task) -> None:
        """Bascule le statut d'une tâche (terminée / à faire)."""
        new_status = "Terminée" if task.status != "Terminée" else "À faire"
        self.service.update_task(task.id, status=new_status)
        self._refresh_tasks_list()
        self.on_update()

    def _add_task(self) -> None:
        """Ouvre le dialogue d'ajout de tâche."""
        dialog = TaskDialog(self, goal_id=self.goal.id, service=self.service, on_save=self._refresh_tasks_list)
        dialog.grab_set()

    def _edit_task(self, task) -> None:
        """Ouvre le dialogue d'édition de tâche."""
        dialog = TaskDialog(self, goal_id=self.goal.id, service=self.service, task=task, on_save=self._refresh_tasks_list)
        dialog.grab_set()

    def _delete_task(self, task) -> None:
        """Supprime une tâche avec confirmation."""
        if messagebox.askyesno("Confirmation", f"Supprimer la tâche '{task.name}' ?"):
            self.service.delete_task(task.id)
            self._refresh_tasks_list()
            self.on_update()

    def _edit_goal(self) -> None:
        """Ouvre le dialogue d'édition du goal."""
        dialog = GoalDialog(self, service=self.service, goal=self.goal, on_save=self.on_update)
        dialog.grab_set()

    def _delete_goal(self) -> None:
        """Supprime le goal avec confirmation."""
        if messagebox.askyesno(
            "Confirmation",
            f"Supprimer le goal '{self.goal.title}' ?\nToutes les tâches associées seront supprimées."
        ):
            self.service.delete_goal(self.goal.id)
            self.on_update()
            # Retour à l'écran vide
            self.destroy()