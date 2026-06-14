"""
ui/dashboard_view.py
Tableau de bord affichant les statistiques globales et les graphiques
de progression avec Matplotlib intégré dans CustomTkinter.
"""

import customtkinter as ctk
from typing import Callable
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from services import GoalService


class DashboardView(ctk.CTkFrame):
    """
    Vue du tableau de bord avec statistiques globales et visualisations.
    S'intègre dans le panneau droit de la fenêtre principale.
    """

    def __init__(
        self,
        master,
        service: GoalService,
        on_navigate_goals: Callable,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)

        self.service = service
        self.on_navigate_goals = on_navigate_goals

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_stats_cards()
        self._build_charts()
        self._build_recent_activity()

    # ───────────────────────────────────────────────
    # En-tête du Dashboard
    # ───────────────────────────────────────────────

    def _build_header(self) -> None:
        """Construit l'en-tête avec titre et bouton de navigation."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=15)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="📊 Tableau de Bord",
            font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="🎯 Voir mes Goals",
            command=self.on_navigate_goals,
            width=150,
            height=35
        ).grid(row=0, column=1, sticky="e")

    # ───────────────────────────────────────────────
    # Cartes de Statistiques
    # ───────────────────────────────────────────────

    def _build_stats_cards(self) -> None:
        """Construit les 6 cartes de statistiques principales."""
        stats = self.service.get_dashboard_stats()

        cards_data = [
            ("🎯", "Goals Total", stats["total_goals"], "#3B82F6"),
            ("✅", "Goals Terminés", stats["goals_completed"], "#10B981"),
            ("🔄", "Goals En Cours", stats["goals_in_progress"], "#F59E0B"),
            ("📋", "Tâches Total", stats["total_tasks"], "#8B5CF6"),
            ("✔️", "Tâches Terminées", stats["completed_tasks"], "#10B981"),
            ("📈", "Progression Globale", f"{stats['global_progress']}%", "#EC4899"),
        ]

        for idx, (icon, label, value, color) in enumerate(cards_data):
            row = idx // 3
            col = idx % 3
            self._create_stat_card(icon, label, value, color, row + 1, col)

    def _create_stat_card(
        self,
        icon: str,
        label: str,
        value,
        color: str,
        row: int,
        col: int
    ) -> None:
        """Crée une carte de statistique individuelle."""
        card = ctk.CTkFrame(self, corner_radius=15)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        # Icône
        ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=32)
        ).pack(pady=(15, 5))

        # Valeur
        ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color
        ).pack(pady=5)

        # Label
        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(pady=(0, 15))

    # ───────────────────────────────────────────────
    # Graphiques Matplotlib
    # ───────────────────────────────────────────────

    def _build_charts(self) -> None:
        """Construit les graphiques de progression."""
        charts_frame = ctk.CTkFrame(self)
        charts_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)

        # Graphique 1 : Répartition des Goals par statut (Camembert)
        self._build_pie_chart(charts_frame, row=0, col=0)

        # Graphique 2 : Progression globale (Jauge)
        self._build_gauge_chart(charts_frame, row=0, col=1)

    def _build_pie_chart(self, parent, row: int, col: int) -> None:
        """Construit un graphique camembert des goals par statut."""
        stats = self.service.get_dashboard_stats()

        labels = ["Non commencé", "En cours", "Terminé"]
        sizes = [
            stats["goals_not_started"],
            stats["goals_in_progress"],
            stats["goals_completed"]
        ]
        colors = ["#9CA3AF", "#F59E0B", "#10B981"]

        # Vérifier qu'il y a des données
        if sum(sizes) == 0:
            frame = ctk.CTkFrame(parent)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(
                frame,
                text="Aucune donnée à afficher",
                text_color="gray"
            ).pack(expand=True)
            return

        # Création de la figure Matplotlib
        fig = Figure(figsize=(5, 4), dpi=100, facecolor="#2B2B2B" if ctk.get_appearance_mode() == "Dark" else "white")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#2B2B2B" if ctk.get_appearance_mode() == "Dark" else "white")

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            textprops={"color": "white" if ctk.get_appearance_mode() == "Dark" else "black"}
        )

        ax.set_title("Répartition des Goals", color="white" if ctk.get_appearance_mode() == "Dark" else "black", fontsize=14, weight="bold")

        # Intégration dans Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def _build_gauge_chart(self, parent, row: int, col: int) -> None:
        """Construit une jauge de progression globale."""
        stats = self.service.get_dashboard_stats()
        progress = stats["global_progress"]

        fig = Figure(figsize=(5, 4), dpi=100, facecolor="#2B2B2B" if ctk.get_appearance_mode() == "Dark" else "white")
        ax = fig.add_subplot(111, projection="polar")
        ax.set_facecolor("#2B2B2B" if ctk.get_appearance_mode() == "Dark" else "white")

        # Jauge semi-circulaire
        theta = [0, progress / 100 * 3.14159, 3.14159]
        radii = [1, 1, 1]
        colors = ["#10B981" if progress >= 50 else "#F59E0B", "#374151", "#374151"]

        ax.barh(1, 3.14159, height=0.3, color="#374151", alpha=0.3)
        ax.barh(1, progress / 100 * 3.14159, height=0.3, color="#10B981" if progress >= 50 else "#F59E0B")

        ax.set_ylim(0, 1.5)
        ax.set_xlim(0, 3.14159)
        ax.set_title(f"Progression Globale\n{progress}%", color="white" if ctk.get_appearance_mode() == "Dark" else "black", fontsize=14, weight="bold", pad=20)

        # Supprimer les axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["polar"].set_visible(False)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    # ───────────────────────────────────────────────
    # Activité Récente
    # ───────────────────────────────────────────────

    def _build_recent_activity(self) -> None:
        """Affiche un aperçu des goals récents."""
        activity_frame = ctk.CTkFrame(self)
        activity_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            activity_frame,
            text="🎯 Goals Récents",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Récupérer les 5 derniers goals
        recent_goals = self.service.list_goals()[:5]

        if not recent_goals:
            ctk.CTkLabel(
                activity_frame,
                text="Aucun goal créé pour le moment",
                text_color="gray"
            ).pack(pady=20)
            return

        for goal in recent_goals:
            row = ctk.CTkFrame(activity_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)

            # Indicateur de statut
            status_colors = {
                "Terminé": "#10B981",
                "En cours": "#F59E0B",
                "Non commencé": "#9CA3AF"
            }
            ctk.CTkLabel(
                row,
                text="●",
                text_color=status_colors.get(goal.status, "gray"),
                font=ctk.CTkFont(size=16)
            ).pack(side="left", padx=(0, 10))

            ctk.CTkLabel(
                row,
                text=goal.title,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")

            progress = self.service.get_goal_progress(goal.id)
            ctk.CTkLabel(
                row,
                text=f"{progress['percentage']:.0f}%",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(side="right")