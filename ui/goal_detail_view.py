"""
ui/goal_detail_view.py
Panneau de détails avec header+progression fusionnés et compactés.
Maximum d'espace pour la liste des tâches.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable
from models.goal import Goal
from services.goal_service import GoalService
from ui.dialogs import GoalDialog, TaskDialog


class GoalDetailView(ctk.CTkFrame):
    """Vue détaillée - Header compact fusionné, tâches en grand."""

    def __init__(
        self,
        master,
        goal: Goal,
        service: GoalService,
        on_update: Callable,
        **kwargs
    ) -> None:
        super().__init__(master, fg_color="#F8FAFC", **kwargs)
        
        self.goal = goal
        self.service = service
        self.on_update = on_update

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # Header fusionné - compact
        self.grid_rowconfigure(1, weight=1)   # Tâches - TOUT l'espace restant

        self._build_fusion_header()
        self._build_tasks_section()

    # ═══════════════════════════════════════════════════
    # HEADER FUSIONNÉ : Titre + Meta + Progression (COMPACT)
    # ═══════════════════════════════════════════════════

    def _build_fusion_header(self) -> None:
        """Carte unique et compacte : titre, meta, barre de progression."""
        card = ctk.CTkFrame(
            self, 
            fg_color="#FFFFFF", 
            corner_radius=16, 
            border_width=1, 
            border_color="#E2E8F0"
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12), padx=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        # ═══ LIGNE 1 : Titre + Badge + Actions ═══
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        # Titre
        ctk.CTkLabel(
            top,
            text=self.goal.title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0F172A"
        ).pack(side="left")

        # Badge priorité (compact)
        priority_colors = {
            "Haute": ("#FEE2E2", "#DC2626"),
            "Moyenne": ("#FEF3C7", "#D97706"),
            "Faible": ("#D1FAE5", "#059669")
        }
        bg, fg = priority_colors.get(self.goal.priority, ("#F1F5F9", "#64748B"))

        badge = ctk.CTkFrame(top, fg_color=bg, corner_radius=6)
        badge.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            badge,
            text=self.goal.priority,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=fg
        ).pack(padx=8, pady=2)

        # Actions (compact, à droite)
        actions = ctk.CTkFrame(top, fg_color="transparent")
        actions.pack(side="right")

        ctk.CTkButton(
            actions,
            text="✏️",
            command=self._edit_goal,
            width=28,
            height=28,
            corner_radius=6,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            actions,
            text="🗑️",
            command=self._delete_goal,
            width=28,
            height=28,
            corner_radius=6,
            fg_color="#FEE2E2",
            hover_color="#FECACA",
            text_color="#DC2626",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        # ═══ LIGNE 2 : Métadonnées (ultra compact) ═══
        meta = ctk.CTkFrame(inner, fg_color="transparent")
        meta.pack(fill="x", pady=(6, 0))

        meta_text = f"📅 {self.goal.created_at.strftime('%d %B %Y')}"
        if self.goal.target_date:
            target_color = "#EF4444" if self.goal.is_overdue else "#3B82F6"
            target_icon = "⚠️" if self.goal.is_overdue else "🎯"
            meta_text += f"   {target_icon} {self.goal.target_date.strftime('%d %B %Y')}"

        ctk.CTkLabel(
            meta,
            text=meta_text,
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(side="left")

        # ═══ LIGNE 3 : Barre de progression + % (une seule ligne) ═══
        progress = self.service.get_goal_progress(self.goal.id)
        percentage = progress["percentage"]
        bar_color = "#10B981" if percentage >= 100 else self.goal.color or "#3B82F6"

        prog_row = ctk.CTkFrame(inner, fg_color="transparent")
        prog_row.pack(fill="x", pady=(10, 0))

        # Barre fine
        bar = ctk.CTkFrame(prog_row, fg_color="#E2E8F0", corner_radius=6, height=6)
        bar.pack(side="left", fill="x", expand=True, padx=(0, 12))
        bar.pack_propagate(False)

        fill_width = max(0.0, min(1.0, percentage / 100.0))
        ctk.CTkFrame(bar, fg_color=bar_color, corner_radius=6).place(
            x=0, y=0, relwidth=fill_width, relheight=1.0
        )

        # Pourcentage compact
        ctk.CTkLabel(
            prog_row,
            text=f"{percentage:.0f}%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=bar_color,
            width=40
        ).pack(side="left")

        # Compteur (droite)
        self.tasks_counter_label = ctk.CTkLabel(
            prog_row,
            text=f"{progress['completed_tasks']}/{progress['total_tasks']}",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.tasks_counter_label.pack(side="right")

    # ═══════════════════════════════════════════════════
    # TÂCHES (GRANDE - prend tout l'espace)
    # ═══════════════════════════════════════════════════

    def _build_tasks_section(self) -> None:
        """Section tâches - MAXIMUM d'espace vertical."""
        card = ctk.CTkFrame(
            self, 
            fg_color="#FFFFFF", 
            corner_radius=16, 
            border_width=1, 
            border_color="#E2E8F0"
        )
        # sticky="nsew" + weight=1 = prend tout l'espace restant
        card.grid(row=1, column=0, sticky="nsew", pady=(0, 4), padx=4)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        # expand=True crucial pour remplir verticalement
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Header compact
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="📋 Tâches",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#0F172A"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="➕ Ajouter",
            command=self._add_task,
            width=100,
            height=30,
            corner_radius=8,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right")

        # Liste qui s'étend verticalement
        self.tasks_scroll = ctk.CTkScrollableFrame(
            inner, 
            fg_color="transparent", 
            label_text=""
        )
        # expand=True = prend tout l'espace vertical disponible
        self.tasks_scroll.pack(fill="both", expand=True, pady=(4, 0))

        self._refresh_tasks_list()

    def _refresh_tasks_list(self) -> None:
        """Recharge les tâches triées."""
        for widget in self.tasks_scroll.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        tasks = self.service.list_tasks(self.goal.id)
        tasks.sort(key=lambda t: t.is_completed)

        if not tasks:
            self._show_empty_state()
            self._update_counter(0, 0)
            return

        has_active = any(not t.is_completed for t in tasks)
        has_completed = any(t.is_completed for t in tasks)
        show_sep = has_active and has_completed

        for i, task in enumerate(tasks):
            if show_sep and task.is_completed and i > 0 and not tasks[i-1].is_completed:
                self._create_separator("Terminées")
            self._create_task_row(task)

        progress = self.service.get_goal_progress(self.goal.id)
        self._update_counter(progress['completed_tasks'], progress['total_tasks'])

    def _show_empty_state(self) -> None:
        """État vide centré verticalement."""
        empty = ctk.CTkFrame(self.tasks_scroll, fg_color="#F8FAFC", corner_radius=12)
        # expand=True pour centrer dans l'espace disponible
        empty.pack(fill="both", expand=True, pady=20)

        ctk.CTkLabel(
            empty,
            text="📝",
            font=ctk.CTkFont(size=40)
        ).pack(expand=True, pady=(0, 8))

        ctk.CTkLabel(
            empty,
            text="Aucune tâche",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#64748B"
        ).pack()

        ctk.CTkLabel(
            empty,
            text="Ajoutez une tâche pour commencer",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        ).pack(pady=(4, 0))

    def _create_separator(self, label_text: str) -> None:
        """Séparateur fin entre sections."""
        frame = ctk.CTkFrame(self.tasks_scroll, fg_color="transparent", height=32)
        frame.pack(fill="x", pady=(4, 2))
        frame.pack_propagate(False)

        line = ctk.CTkFrame(frame, fg_color="#E2E8F0", height=1)
        line.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#94A3B8",
            fg_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _create_task_row(self, task) -> None:
        """Ligne de tâche compacte et moderne."""
        bg_color = "#F8FAFC" if not task.is_completed else "#F1F5F9"

        row = ctk.CTkFrame(
            self.tasks_scroll, 
            fg_color=bg_color, 
            corner_radius=10,
            border_width=1,
            border_color="#E2E8F0"
        )
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        row.configure(height=56)

        # Checkbox
        if task.is_completed:
            check = ctk.CTkButton(
                row,
                text="✓",
                width=24,
                height=24,
                corner_radius=6,
                fg_color="#10B981",
                hover_color="#059669",
                text_color="#FFFFFF",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda t=task: self._toggle_task(t)
            )
        else:
            check = ctk.CTkButton(
                row,
                text="",
                width=24,
                height=24,
                corner_radius=6,
                fg_color="#E2E8F0",
                hover_color="#CBD5E1",
                text_color="#E2E8F0",
                command=lambda t=task: self._toggle_task(t)
            )
        check.pack(side="left", padx=(12, 10), pady=10)

        # Texte
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, pady=10)

        name_color = "#94A3B8" if task.is_completed else "#0F172A"
        font = ctk.CTkFont(
            size=13,
            weight="normal" if task.is_completed else "bold",
            overstrike=task.is_completed
        )

        ctk.CTkLabel(
            text_frame,
            text=task.name,
            font=font,
            text_color=name_color,
            anchor="w"
        ).pack(fill="x")

        # Badge statut (droite)
        if task.is_completed:
            badge = ctk.CTkFrame(row, fg_color="#D1FAE5", corner_radius=4)
            badge.pack(side="right", padx=(0, 8))
            ctk.CTkLabel(
                badge,
                text="✓",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#059669"
            ).pack(padx=6, pady=2)
        else:
            status_colors = {
                "À faire":   ("#FEF3C7", "#D97706"),
                "En cours":  ("#DBEAFE", "#3B82F6"),
            }
            sbg, sfg = status_colors.get(task.status, ("#F1F5F9", "#64748B"))
            
            badge = ctk.CTkFrame(row, fg_color=sbg, corner_radius=4)
            badge.pack(side="right", padx=(0, 8))
            ctk.CTkLabel(
                badge,
                text=task.status,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=sfg
            ).pack(padx=6, pady=2)

        # Actions
        if not task.is_completed:
            ctk.CTkButton(
                row,
                text="✏️",
                width=24,
                height=24,
                corner_radius=4,
                fg_color="transparent",
                hover_color="#E2E8F0",
                text_color="#64748B",
                font=ctk.CTkFont(size=11),
                command=lambda t=task: self._edit_task(t)
            ).pack(side="right", padx=(0, 2), pady=10)

        ctk.CTkButton(
            row,
            text="🗑️",
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color="#EF4444",
            font=ctk.CTkFont(size=11),
            command=lambda t=task: self._delete_task(t)
        ).pack(side="right", padx=(0, 10), pady=10)

    # ═══════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════

    def _update_counter(self, completed: int, total: int) -> None:
        """Met à jour le compteur dans le header."""
        if hasattr(self, 'tasks_counter_label'):
            self.tasks_counter_label.configure(text=f"{completed}/{total}")

    def _toggle_task(self, task) -> None:
        new_status = "Terminée" if task.status != "Terminée" else "À faire"
        self.service.update_task(task.id, status=new_status)
        self._refresh_tasks_list()
        self.on_update()

    def _add_task(self) -> None:
        dialog = TaskDialog(self, goal_id=self.goal.id, service=self.service, on_save=self._refresh_tasks_list)
        dialog.grab_set()

    def _edit_task(self, task) -> None:
        dialog = TaskDialog(self, goal_id=self.goal.id, service=self.service, task=task, on_save=self._refresh_tasks_list)
        dialog.grab_set()

    def _delete_task(self, task) -> None:
        if messagebox.askyesno("Confirmation", f"Supprimer '{task.name}' ?"):
            self.service.delete_task(task.id)
            self._refresh_tasks_list()
            self.on_update()

    def _edit_goal(self) -> None:
        dialog = GoalDialog(self, service=self.service, goal=self.goal, on_save=self.on_update)
        dialog.grab_set()

    def _delete_goal(self) -> None:
        if messagebox.askyesno(
            "Confirmation",
            f"Supprimer '{self.goal.title}' ?\nToutes les tâches seront supprimées."
        ):
            self.service.delete_goal(self.goal.id)
            self.on_update()
            try:
                self.destroy()
            except Exception:
                pass