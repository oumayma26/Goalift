"""
ui/dashboard_view.py
Tableau de bord avec style Glassmorphism et statistiques temporelles.
"""

import customtkinter as ctk
from typing import Callable
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rcParams
import numpy as np
from services.goal_service import GoalService
# Import matplotlib
import matplotlib.pyplot as plt

# Configuration Matplotlib pour thème clair
rcParams['text.color'] = '#1E293B'
rcParams['axes.labelcolor'] = '#475569'
rcParams['xtick.color'] = '#64748B'
rcParams['ytick.color'] = '#64748B'
rcParams['axes.edgecolor'] = '#E2E8F0'
rcParams['axes.facecolor'] = '#FFFFFF'
rcParams['figure.facecolor'] = '#F8FAFC'


class DashboardView(ctk.CTkFrame):
    """
    Vue du tableau de bord avec style Glassmorphism.
    """

    def __init__(
        self,
        master,
        service: GoalService,
        on_navigate_goals: Callable,
        **kwargs
    ) -> None:
        super().__init__(master, fg_color="#F1F5F9", **kwargs)

        self.service = service
        self.on_navigate_goals = on_navigate_goals

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_stats_cards()
        self._build_charts()

    # ───────────────────────────────────────────────
    # En-tête
    # ───────────────────────────────────────────────

    def _build_header(self) -> None:
        """En-tête du dashboard."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="📊 Tableau de bord",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="🎯 Voir mes objectifs",
            command=self.on_navigate_goals,
            width=160,
            height=40,
            corner_radius=12,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="right")

    # ───────────────────────────────────────────────
    # Cartes de statistiques (Glassmorphism)
    # ───────────────────────────────────────────────

    def _build_stats_cards(self) -> None:
        """Cartes de stats avec style glassmorphism."""
        yearly = self.service.get_yearly_stats()
        monthly = self.service.get_monthly_stats()
        current_year = __import__('datetime').datetime.now().year

        cards_data = [
            {
                "icon": "🏆",
                "label": f"Terminés {current_year}",
                "value": str(yearly["completed"]),
                "color": "#10B981",
                "gradient": ("#D1FAE5", "#FFFFFF")
            },
            {
                "icon": "📝",
                "label": f"Créés {current_year}",
                "value": str(yearly["created"]),
                "color": "#3B82F6",
                "gradient": ("#DBEAFE", "#FFFFFF")
            },
            {
                "icon": "🔄",
                "label": "En cours ce mois",
                "value": str(monthly["in_progress"]),
                "color": "#F59E0B",
                "gradient": ("#FEF3C7", "#FFFFFF")
            },
        ]

        for idx, card_data in enumerate(cards_data):
            self._create_glass_card(card_data, row=1, col=idx)

    def _create_glass_card(self, data: dict, row: int, col: int) -> None:
        """Crée une carte avec effet glassmorphism."""
        card = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=1,
            border_color="#E2E8F0"
        )
        card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

        # Ombre simulée par un frame derrière
        shadow = ctk.CTkFrame(
            self,
            fg_color="#000000",
            corner_radius=20
        )
        # On ne peut pas vraiment faire d'ombre avec CTk, on utilise le border

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        # Icône + valeur sur la même ligne
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=data["icon"],
            font=ctk.CTkFont(size=32)
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=data["value"],
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=data["color"]
        ).pack(side="right")

        # Label
        ctk.CTkLabel(
            inner,
            text=data["label"],
            font=ctk.CTkFont(size=13),
            text_color="#64748B"
        ).pack(anchor="w", pady=(10, 0))

    # ───────────────────────────────────────────────
    # Graphiques
    # ───────────────────────────────────────────────

    def _build_charts(self) -> None:
        """Construit les graphiques en style glassmorphism."""
        charts_container = ctk.CTkFrame(self, fg_color="transparent")
        charts_container.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=12, pady=12)
        charts_container.grid_columnconfigure((0, 1), weight=1)
        charts_container.grid_rowconfigure(0, weight=1)

        # Graphique 1 : Donut - Répartition par statut
        self._build_donut_chart(charts_container, row=0, col=0)

        # Graphique 2 : Courbe - Progression 30 jours
        self._build_line_chart(charts_container, row=0, col=1)

    def _build_donut_chart(self, parent, row: int, col: int) -> None:
        """Graphique donut avec répartition par statut."""
        distribution = self.service.get_status_distribution()

        labels = []
        sizes = []
        colors = []

        color_map = {
            "Terminé": "#10B981",
            "En cours": "#3B82F6",
            "Non commencé": "#94A3B8"
        }

        for status in ["Terminé", "En cours", "Non commencé"]:
            if status in distribution and distribution[status] > 0:
                labels.append(status)
                sizes.append(distribution[status])
                colors.append(color_map.get(status, "#CBD5E1"))

        if not sizes or sum(sizes) == 0:
            self._build_empty_chart(parent, "Répartition par statut", row, col)
            return

        # Carte glassmorphism
        card = self._create_chart_card(parent, "🍩 Répartition par statut")
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        fig = Figure(figsize=(5, 4.5), dpi=100, facecolor="#FFFFFF")
        ax = fig.add_subplot(111)

        # Donut chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.0f%%',
            startangle=90,
            pctdistance=0.75,
            textprops={'fontsize': 11, 'fontweight': 'bold', 'color': '#1E293B'}
        )

        # Cercle blanc au centre pour effet donut
        centre_circle = plt.Circle((0, 0), 0.50, fc='#FFFFFF')
        ax.add_artist(centre_circle)

        # Texte au centre
        total = sum(sizes)
        ax.text(0, 0.05, str(total), ha='center', va='center', 
                fontsize=28, fontweight='bold', color='#1E293B')
        ax.text(0, -0.15, 'goals', ha='center', va='center', 
                fontsize=12, color='#64748B')

        ax.axis('equal')

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def _build_line_chart(self, parent, row: int, col: int) -> None:
        """Courbe de progression sur 30 jours."""
        daily_data = self.service.get_daily_progress_30_days()

        dates = [d["date"] for d in daily_data]
        values = [d["completed_tasks"] for d in daily_data]

        # Calculer la progression cumulative
        cumulative = []
        total = 0
        for v in values:
            total += v
            cumulative.append(total)

        card = self._create_chart_card(parent, "📈 Progression sur 30 jours")
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        fig = Figure(figsize=(5, 4.5), dpi=100, facecolor="#FFFFFF")
        ax = fig.add_subplot(111)

        # Fond de la zone de tracé
        ax.set_facecolor("#FAFBFC")

        # Courbe avec dégradé visuel
        x = np.arange(len(dates))
        ax.fill_between(x, cumulative, alpha=0.15, color="#3B82F6")
        ax.plot(x, cumulative, color="#3B82F6", linewidth=2.5, marker='o', 
                markersize=4, markerfacecolor="#FFFFFF", markeredgecolor="#3B82F6",
                markeredgewidth=2)

        # Grille subtile
        ax.grid(True, alpha=0.3, color="#E2E8F0", linestyle='--')
        ax.set_axisbelow(True)

        # Labels X (tous les 5 jours pour lisibilité)
        tick_positions = list(range(0, len(dates), 5))
        tick_labels = [dates[i] for i in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=0, fontsize=9)

        ax.set_ylabel('Tâches terminées (cumul)', fontsize=10, color='#475569')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Titre dans le graphique
        ax.set_title(f"Total: {cumulative[-1]} tâches terminées", 
                    fontsize=12, color='#64748B', pad=10)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def _create_chart_card(self, parent, title: str) -> ctk.CTkFrame:
        """Crée une carte glassmorphism pour un graphique."""
        card = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=20,
            border_width=1,
            border_color="#E2E8F0"
        )

        # Titre de la carte
        header = ctk.CTkFrame(card, fg_color="transparent", height=40)
        header.pack(fill="x", padx=20, pady=(15, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        return card

    def _build_empty_chart(self, parent, title: str, row: int, col: int) -> None:
        """Affiche un message quand il n'y a pas de données."""
        card = self._create_chart_card(parent, title)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(
            card,
            text="Aucune donnée à afficher",
            font=ctk.CTkFont(size=14),
            text_color="#94A3B8"
        ).pack(expand=True, pady=80)


