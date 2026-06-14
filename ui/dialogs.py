"""
ui/dialogs.py
Dialogues modaux - Thème CLAIR.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Callable
from models import Goal, Task
from services import GoalService


class GoalDialog(ctk.CTkToplevel):
    """Dialogue Goal - Design clair."""

    def __init__(
        self,
        master,
        service: GoalService,
        goal: Optional[Goal] = None,
        on_save: Optional[Callable] = None
    ) -> None:
        super().__init__(master)

        self.service = service
        self.goal = goal
        self.on_save = on_save
        self.is_edit = goal is not None

        self.title("Modifier l'objectif" if self.is_edit else "Nouvel objectif")
        self.geometry("500x520")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        self._build_form()

        if self.is_edit:
            self._fill_form()

    def _build_form(self) -> None:
        # Utiliser grid sur le toplevel directement
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Zone scrollable pour le contenu
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF", corner_radius=0)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        # Titre du dialogue
        ctk.CTkLabel(
            scroll_frame,
            text="Modifier l'objectif" if self.is_edit else "Nouvel objectif",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", pady=(0, 15))

        # Titre
        ctk.CTkLabel(
            scroll_frame,
            text="Titre *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.title_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="Nom de l'objectif...",
            height=38,
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.title_entry.pack(fill="x", pady=(0, 12))

        # Description
        ctk.CTkLabel(
            scroll_frame,
            text="Description",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.desc_text = ctk.CTkTextbox(
            scroll_frame,
            height=70,
            wrap="word",
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.desc_text.pack(fill="x", pady=(0, 12))

        # Date cible
        ctk.CTkLabel(
            scroll_frame,
            text="Date cible (AAAA-MM-JJ)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.target_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="Optionnel...",
            height=38,
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.target_entry.pack(fill="x", pady=(0, 12))

        # Priorité
        ctk.CTkLabel(
            scroll_frame,
            text="Priorité",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.priority_var = ctk.StringVar(value="Moyenne")
        # CTkSegmentedButton avec arguments compatibles
        priorities = ctk.CTkSegmentedButton(
            scroll_frame,
            values=["Faible", "Moyenne", "Haute"],
            variable=self.priority_var,
            height=35,
            corner_radius=8,
            fg_color="#F1F5F9",
            selected_color="#3B82F6",
            selected_hover_color="#2563EB",
            unselected_color="#F1F5F9",
            unselected_hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        priorities.pack(fill="x", pady=(0, 12))

        # Statut (édition uniquement)
        if self.is_edit:
            ctk.CTkLabel(
                scroll_frame,
                text="Statut",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#475569"
            ).pack(anchor="w", pady=(0, 5))

            self.status_var = ctk.StringVar(value=self.goal.status if self.goal else "Non commencé")
            ctk.CTkOptionMenu(
                scroll_frame,
                values=["Non commencé", "En cours", "Terminé"],
                variable=self.status_var,
                height=38,
                corner_radius=8,
                fg_color="#F8FAFC",
                button_color="#E2E8F0",
                text_color="#1E293B",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#1E293B",
                dropdown_hover_color="#F1F5F9",
                font=ctk.CTkFont(size=12)
            ).pack(fill="x", pady=(0, 12))

        # Boutons fixes en bas (hors scrollable)
        btn_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.grid_propagate(False)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        # Ligne de séparation
        ctk.CTkFrame(btn_frame, height=1, fg_color="#E2E8F0").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15)
        )

        # Bouton Annuler
        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Annuler",
            command=self.destroy,
            height=40,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Bouton Enregistrer
        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Enregistrer",
            command=self._save,
            height=40,
            corner_radius=8,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_save.grid(row=1, column=1, sticky="ew", padx=(8, 0))

    def _fill_form(self) -> None:
        if not self.goal:
            return

        self.title_entry.insert(0, self.goal.title)
        self.desc_text.insert("0.0", self.goal.description)
        if self.goal.target_date:
            self.target_entry.insert(0, self.goal.target_date.strftime("%Y-%m-%d"))
        self.priority_var.set(self.goal.priority)

    def _save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return

        description = self.desc_text.get("0.0", "end").strip()
        target_date = self.target_entry.get().strip() or None
        priority = self.priority_var.get()

        try:
            if self.is_edit:
                status = self.status_var.get()
                self.service.update_goal(
                    self.goal.id,
                    title=title,
                    description=description,
                    target_date=target_date,
                    priority=priority,
                    status=status
                )
            else:
                self.service.create_goal(
                    title=title,
                    description=description,
                    target_date=target_date,
                    priority=priority
                )

            if self.on_save:
                self.on_save()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erreur", str(e))


class TaskDialog(ctk.CTkToplevel):
    """Dialogue Task - Design clair."""

    def __init__(
        self,
        master,
        goal_id: int,
        service: GoalService,
        task: Optional[Task] = None,
        on_save: Optional[Callable] = None
    ) -> None:
        super().__init__(master)

        self.goal_id = goal_id
        self.service = service
        self.task = task
        self.on_save = on_save
        self.is_edit = task is not None

        self.title("Modifier la tâche" if self.is_edit else "Nouvelle tâche")
        self.geometry("480x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        self._build_form()

        if self.is_edit:
            self._fill_form()

    def _build_form(self) -> None:
        # Grid sur le toplevel
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Zone scrollable
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF", corner_radius=0)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            scroll_frame,
            text="Modifier la tâche" if self.is_edit else "Nouvelle tâche",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", pady=(0, 15))

        # Nom
        ctk.CTkLabel(
            scroll_frame,
            text="Nom de la tâche *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.name_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="Nom...",
            height=38,
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.name_entry.pack(fill="x", pady=(0, 12))

        # Description
        ctk.CTkLabel(
            scroll_frame,
            text="Description",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.desc_text = ctk.CTkTextbox(
            scroll_frame,
            height=60,
            wrap="word",
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.desc_text.pack(fill="x", pady=(0, 12))

        # Statut (édition)
        if self.is_edit:
            ctk.CTkLabel(
                scroll_frame,
                text="Statut",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#475569"
            ).pack(anchor="w", pady=(0, 5))

            self.status_var = ctk.StringVar(value=self.task.status if self.task else "À faire")
            ctk.CTkOptionMenu(
                scroll_frame,
                values=["À faire", "En cours", "Terminée"],
                variable=self.status_var,
                height=38,
                corner_radius=8,
                fg_color="#F8FAFC",
                button_color="#E2E8F0",
                text_color="#1E293B",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#1E293B",
                dropdown_hover_color="#F1F5F9",
                font=ctk.CTkFont(size=12)
            ).pack(fill="x", pady=(0, 12))

        # Boutons fixes en bas
        btn_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.grid_propagate(False)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkFrame(btn_frame, height=1, fg_color="#E2E8F0").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15)
        )

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Annuler",
            command=self.destroy,
            height=40,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Enregistrer",
            command=self._save,
            height=40,
            corner_radius=8,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_save.grid(row=1, column=1, sticky="ew", padx=(8, 0))

    def _fill_form(self) -> None:
        if not self.task:
            return
        self.name_entry.insert(0, self.task.name)
        self.desc_text.insert("0.0", self.task.description)

    def _save(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom est obligatoire")
            return

        description = self.desc_text.get("0.0", "end").strip()

        try:
            if self.is_edit:
                status = self.status_var.get()
                self.service.update_task(
                    self.task.id,
                    name=name,
                    description=description,
                    status=status
                )
            else:
                self.service.create_task(
                    goal_id=self.goal_id,
                    name=name,
                    description=description
                )

            if self.on_save:
                self.on_save()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erreur", str(e))