"""
ui/main_window.py
Fenêtre principale avec thème CLAIR et moderne.
"""

import customtkinter as ctk
from typing import Optional
from services import GoalService
from database import DatabaseManager
from ui.theme_manager import ThemeManager
from ui.dashboard_view import DashboardView
from ui.goal_detail_view import GoalDetailView
from ui.dialogs import GoalDialog


class MainWindow(ctk.CTk):
    """
    Fenêtre principale - Design clair, épuré et professionnel.
    """

    def __init__(self) -> None:
        super().__init__()

        # Configuration fenêtre
        self.title("Goals Manager")
        self.geometry("1280x850")
        self.minsize(1000, 700)
        self.configure(fg_color="#F1F5F9")  # Fond gris très clair

        self.db = DatabaseManager()
        self.service = GoalService(self.db)
        self.selected_goal_id: Optional[int] = None
        self.current_view: Optional[ctk.CTkFrame] = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

        self._show_dashboard()

    def _build_left_panel(self) -> None:
        """Panneau gauche - Sidebar claire et élégante."""
        self.left_frame = ctk.CTkFrame(
            self,
            width=320,
            fg_color="#FFFFFF",
            corner_radius=0,
            border_width=0
        )
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.left_frame.grid_rowconfigure(6, weight=1)
        self.left_frame.grid_propagate(False)

        # Logo / Titre
        header = ctk.CTkFrame(self.left_frame, fg_color="transparent", height=70)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="🎯",
            font=ctk.CTkFont(size=28)
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header,
            text="Goals Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        # Navigation
        nav_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)

        self.dashboard_btn = self._create_nav_button(
            nav_frame, "📊 Tableau de bord", self._show_dashboard, active=True
        )
        self.dashboard_btn.pack(fill="x", pady=3)

        self.goals_btn = self._create_nav_button(
            nav_frame, "🎯 Mes Objectifs", self._show_goals_view, active=False
        )
        self.goals_btn.pack(fill="x", pady=3)

        # Séparateur
        ctk.CTkFrame(self.left_frame, height=1, fg_color="#E2E8F0").grid(
            row=2, column=0, sticky="ew", padx=20, pady=15
        )

        # Section Filtres
        filter_label = ctk.CTkLabel(
            self.left_frame,
            text="FILTRES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8"
        )
        filter_label.grid(row=3, column=0, padx=20, pady=(5, 10), sticky="w")

        # Recherche
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_goals_list())

        search_frame = ctk.CTkFrame(self.left_frame, fg_color="#F1F5F9", corner_radius=10)
        search_frame.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Rechercher...",
            textvariable=self.search_var,
            fg_color="transparent",
            border_width=0,
            height=40
        ).pack(fill="x", padx=10, pady=5)

        # Filtres statut/priorité
        filters_row = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        filters_row.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        filters_row.grid_columnconfigure((0, 1), weight=1)

        self.status_filter = ctk.CTkOptionMenu(
            filters_row,
            values=["Tous", "Non commencé", "En cours", "Terminé"],
            command=lambda _: self.refresh_goals_list(),
            width=130,
            fg_color="#F1F5F9",
            button_color="#E2E8F0",
            text_color="#475569",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#1E293B",
            dropdown_hover_color="#F1F5F9"
        )
        self.status_filter.set("Tous")
        self.status_filter.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.priority_filter = ctk.CTkOptionMenu(
            filters_row,
            values=["Toutes", "Faible", "Moyenne", "Haute"],
            command=lambda _: self.refresh_goals_list(),
            width=130,
            fg_color="#F1F5F9",
            button_color="#E2E8F0",
            text_color="#475569",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#1E293B",
            dropdown_hover_color="#F1F5F9"
        )
        self.priority_filter.set("Toutes")
        self.priority_filter.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Liste des goals
        self.goals_scroll = ctk.CTkScrollableFrame(
            self.left_frame,
            fg_color="transparent",
            label_text=""
        )
        self.goals_scroll.grid(row=6, column=0, sticky="nsew", padx=10, pady=10)

        # Bouton Nouveau Goal
        self.new_goal_btn = ctk.CTkButton(
            self.left_frame,
            text="➕ Nouvel objectif",
            command=self._open_new_goal_dialog,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF"
        )
        self.new_goal_btn.grid(row=7, column=0, padx=15, pady=(5, 20), sticky="ew")

    def _create_nav_button(self, parent, text, command, active=False):
        """Crée un bouton de navigation stylisé."""
        colors = {
            "active": {"fg": "#EFF6FF", "text": "#3B82F6", "hover": "#EFF6FF"},
            "inactive": {"fg": "transparent", "text": "#64748B", "hover": "#F1F5F9"}
        }
        state = "active" if active else "inactive"

        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold" if active else "normal"),
            fg_color=colors[state]["fg"],
            hover_color=colors[state]["hover"],
            text_color=colors[state]["text"],
            anchor="w",
            text_color_disabled=colors[state]["text"]
        )
        return btn

    def _build_right_panel(self) -> None:
        """Panneau droit - Fond clair."""
        self.right_frame = ctk.CTkFrame(
            self,
            fg_color="#F1F5F9",
            corner_radius=0,
            border_width=0
        )
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

    def _clear_right_panel(self) -> None:
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def _show_dashboard(self) -> None:
        self._clear_right_panel()
        self.dashboard_btn.configure(
            fg_color="#EFF6FF", text_color="#3B82F6", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.goals_btn.configure(
            fg_color="transparent", text_color="#64748B", font=ctk.CTkFont(size=13, weight="normal")
        )

        self.current_view = DashboardView(
            self.right_frame,
            service=self.service,
            on_navigate_goals=self._show_goals_view
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _show_goals_view(self) -> None:
        self._clear_right_panel()
        self.dashboard_btn.configure(
            fg_color="transparent", text_color="#64748B", font=ctk.CTkFont(size=13, weight="normal")
        )
        self.goals_btn.configure(
            fg_color="#EFF6FF", text_color="#3B82F6", font=ctk.CTkFont(size=13, weight="bold")
        )

        self.empty_label = ctk.CTkLabel(
            self.right_frame,
            text="Sélectionnez un objectif pour voir les détails",
            font=ctk.CTkFont(size=16),
            text_color="#94A3B8"
        )
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

        self.selected_goal_id = None
        self.refresh_goals_list()

    def refresh_goals_list(self) -> None:
        for widget in self.goals_scroll.winfo_children():
            widget.destroy()

        status = self.status_filter.get()
        priority = self.priority_filter.get()
        search = self.search_var.get() or None

        if status == "Tous":
            status = None
        if priority == "Toutes":
            priority = None

        goals = self.service.list_goals(status=status, priority=priority, search=search)

        if not goals:
            ctk.CTkLabel(
                self.goals_scroll,
                text="Aucun objectif trouvé",
                text_color="#94A3B8",
                font=ctk.CTkFont(size=13)
            ).pack(pady=30)
            return

        for goal in goals:
            self._create_goal_card(goal)

    def _create_goal_card(self, goal) -> None:
        """Carte de goal - Design clair et moderne."""
        priority_colors = {
            "Haute": "#FEE2E2",
            "Moyenne": "#FEF3C7",
            "Faible": "#D1FAE5"
        }
        priority_text_colors = {
            "Haute": "#DC2626",
            "Moyenne": "#D97706",
            "Faible": "#059669"
        }

        card = ctk.CTkFrame(
            self.goals_scroll,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E2E8F0"
        )
        card.pack(fill="x", padx=5, pady=4)
        card.bind("<Button-1>", lambda e, gid=goal.id: self._select_goal(gid))
        card.configure(cursor="hand2")

        # En-tête carte
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 8))

        # Badge priorité
        priority_badge = ctk.CTkLabel(
            header,
            text=f"  {goal.priority}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=priority_colors.get(goal.priority, "#F1F5F9"),
            text_color=priority_text_colors.get(goal.priority, "#64748B"),
            corner_radius=6
        )
        priority_badge.pack(side="right")

        # Titre
        title = ctk.CTkLabel(
            header,
            text=goal.title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1E293B",
            anchor="w"
        )
        title.pack(side="left", fill="x", expand=True)
        title.bind("<Button-1>", lambda e, gid=goal.id: self._select_goal(gid))

        # Description (si présente)
        if goal.description:
            desc = ctk.CTkLabel(
                card,
                text=goal.description[:60] + "..." if len(goal.description) > 60 else goal.description,
                font=ctk.CTkFont(size=12),
                text_color="#64748B",
                anchor="w"
            )
            desc.pack(fill="x", padx=15, pady=(0, 8))

        # Barre de progression
        progress = self.service.get_goal_progress(goal.id)
        progress_frame = ctk.CTkFrame(card, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Barre moderne
        progress_bar_bg = ctk.CTkFrame(progress_frame, height=6, corner_radius=3, fg_color="#E2E8F0")
        progress_bar_bg.pack(fill="x", expand=True, side="left", padx=(0, 10))

        progress_bar = ctk.CTkProgressBar(
            progress_bar_bg,
            height=6,
            corner_radius=3,
            fg_color="#E2E8F0",
            progress_color="#3B82F6",
            width=200
        )
        progress_bar.pack(fill="x", padx=0, pady=0)
        progress_bar.set(progress["percentage"] / 100)

        # Pourcentage
        ctk.CTkLabel(
            progress_frame,
            text=f"{progress['percentage']:.0f}%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3B82F6",
            width=40
        ).pack(side="right")

        # Footer
        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=(0, 12))

        # Statut avec dot coloré
        status_colors = {
            "Terminé": "#10B981",
            "En cours": "#F59E0B",
            "Non commencé": "#94A3B8"
        }
        dot_color = status_colors.get(goal.status, "#94A3B8")

        status_frame = ctk.CTkFrame(footer, fg_color="transparent")
        status_frame.pack(side="left")

        ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=dot_color
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            status_frame,
            text=goal.status,
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(side="left")

        # Nombre de tâches
        ctk.CTkLabel(
            footer,
            text=f"{progress['total_tasks']} tâches",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(side="right")

        # Highlight si sélectionné
        if goal.id == self.selected_goal_id:
            card.configure(border_color="#3B82F6", border_width=2)

    def _select_goal(self, goal_id: int) -> None:
        self.selected_goal_id = goal_id
        self.refresh_goals_list()
        self._show_goal_details(goal_id)

    def _show_goal_details(self, goal_id: int) -> None:
        goal = self.service.get_goal(goal_id)
        if not goal:
            return

        self._clear_right_panel()

        self.current_view = GoalDetailView(
            self.right_frame,
            goal=goal,
            service=self.service,
            on_update=self.refresh_goals_list
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _open_new_goal_dialog(self) -> None:
        dialog = GoalDialog(self, service=self.service, on_save=self.refresh_goals_list)
        dialog.grab_set()

    def run(self) -> None:
        self.mainloop()