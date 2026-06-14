"""
ui/goals_grid_view.py
Grille responsive de cards Goal avec tri par progression.
"""

import os
import customtkinter as ctk
from typing import Callable, List
from PIL import Image
from models import Goal
from services import GoalService


class GoalsGridView(ctk.CTkFrame):
    """
    Vue grille de goals — 3 colonnes, cards fluides, tri par progression.
    """

    def __init__(
        self,
        master,
        service: GoalService,
        goals: List[Goal],
        on_select_goal: Callable,
        **kwargs
    ) -> None:
        super().__init__(master, fg_color="#F1F5F9", **kwargs)

        self.service = service
        self.on_select_goal = on_select_goal
        self.goals = goals

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_grid()

    def _build_header(self) -> None:
        """En-tête avec titre et compteur."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))

        ctk.CTkLabel(
            header,
            text=f"🎯 Objectifs ({len(self.goals)})",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

    def _build_grid(self) -> None:
        """Construit la grille de cards."""
        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            label_text=""
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll.grid_columnconfigure((0, 1, 2), weight=1)

        if not self.goals:
            self._build_empty_state()
            return

        for idx, goal in enumerate(self.goals):
            self._create_goal_card(goal, idx)

    def _build_empty_state(self) -> None:
        """État vide."""
        empty = ctk.CTkFrame(self.scroll, fg_color="transparent")
        empty.grid(row=0, column=0, columnspan=3, pady=100)

        ctk.CTkLabel(
            empty,
            text="📭 Aucun objectif",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#94A3B8"
        ).pack()
        ctk.CTkLabel(
            empty,
            text="Créez votre premier objectif pour commencer !",
            font=ctk.CTkFont(size=13),
            text_color="#CBD5E1"
        ).pack(pady=(5, 0))

    def _create_goal_card(self, goal: Goal, index: int) -> None:
        """Crée une card Goal complète."""
        progress = self.service.get_goal_progress(goal.id)
        percentage = progress["percentage"]
        goal_color = goal.color or "#3B82F6"

        row = index // 3
        col = index % 3

        # Card container
        card = ctk.CTkFrame(
            self.scroll,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E2E8F0",
            height=300
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)
        card.bind("<Enter>", lambda e, c=card, gc=goal_color: self._on_card_enter(c, gc))
        card.bind("<Leave>", lambda e, c=card: self._on_card_leave(c))
        card.bind("<Button-1>", lambda e, gid=goal.id: self.on_select_goal(gid))
        card.configure(cursor="hand2")

        # ─── IMAGE / PLACEHOLDER ───
        img_frame = ctk.CTkFrame(card, fg_color="transparent", height=120, corner_radius=16)
        img_frame.pack(fill="x", padx=0, pady=0)
        img_frame.pack_propagate(False)
        img_frame.bind("<Button-1>", lambda e, gid=goal.id: self.on_select_goal(gid))

        if goal.image_path and os.path.exists(goal.image_path):
            try:
                img = Image.open(goal.image_path)
                img = img.convert("RGB")
                # Crop center pour ratio 16:9
                w, h = img.size
                target_ratio = 16 / 9
                current_ratio = w / h
                if current_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    left = (w - new_w) // 2
                    img = img.crop((left, 0, left + new_w, h))
                else:
                    new_h = int(w / target_ratio)
                    top = (h - new_h) // 2
                    img = img.crop((0, top, w, top + new_h))

                img = img.resize((340, 120), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(340, 120))
                img_label = ctk.CTkLabel(img_frame, text="", image=ctk_img, corner_radius=16)
                img_label.pack(fill="both", expand=True)
                img_label.bind("<Button-1>", lambda e, gid=goal.id: self.on_select_goal(gid))
            except Exception:
                self._build_placeholder(img_frame, goal, goal_color)
        else:
            self._build_placeholder(img_frame, goal, goal_color)

        # ─── BANDE COULEUR ───
        color_bar = ctk.CTkFrame(card, height=4, fg_color=goal_color, corner_radius=0)
        color_bar.pack(fill="x", padx=0, pady=0)

        # ─── CONTENU ───
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=12)
        content.bind("<Button-1>", lambda e, gid=goal.id: self.on_select_goal(gid))

        # Titre + priorité
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack(fill="x")
        title_row.bind("<Button-1>", lambda e, gid=goal.id: self.on_select_goal(gid))

        ctk.CTkLabel(
            title_row,
            text=goal.title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1E293B",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        priority_colors = {
            "Haute": ("#FEE2E2", "#DC2626"),
            "Moyenne": ("#FEF3C7", "#D97706"),
            "Faible": ("#D1FAE5", "#059669")
        }
        bg, fg = priority_colors.get(goal.priority, ("#F1F5F9", "#64748B"))
        ctk.CTkLabel(
            title_row,
            text=f"  {goal.priority}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=bg,
            text_color=fg,
            corner_radius=6
        ).pack(side="right")

        # Description
        if goal.description:
            desc_text = goal.description[:60] + "..." if len(goal.description) > 60 else goal.description
            ctk.CTkLabel(
                content,
                text=desc_text,
                font=ctk.CTkFont(size=12),
                text_color="#64748B",
                anchor="w",
                wraplength=280
            ).pack(fill="x", pady=(6, 0))

        # ─── BARRE DE PROGRESSION ───
        progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(12, 4))

        # Label %
        percent_color = "#10B981" if percentage >= 100 else goal_color
        ctk.CTkLabel(
            progress_frame,
            text=f"{percentage:.0f}%",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=percent_color
        ).pack(side="right")

        ctk.CTkLabel(
            progress_frame,
            text="Progression",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(side="left")

        # Barre
        bar_bg = ctk.CTkFrame(content, height=8, corner_radius=4, fg_color="#E2E8F0")
        bar_bg.pack(fill="x", pady=(0, 8))
        bar_bg.pack_propagate(False)

        fill_width = max(1, int(300 * (percentage / 100))) if percentage > 0 else 1
        bar_fill = ctk.CTkFrame(
            bar_bg,
            height=8,
            corner_radius=4,
            fg_color=percent_color,
            width=fill_width
        )
        bar_fill.pack(side="left", fill="y")

        # ─── FOOTER ───
        footer = ctk.CTkFrame(content, fg_color="transparent")
        footer.pack(fill="x", pady=(4, 0))

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

        ctk.CTkLabel(
            footer,
            text=f"{progress['completed_tasks']}/{progress['total_tasks']} tâches",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(side="right")

    def _build_placeholder(self, parent, goal: Goal, color: str) -> None:
        """Placeholder avec initiales du titre."""
        placeholder = ctk.CTkFrame(parent, fg_color=color, corner_radius=16)
        placeholder.pack(fill="both", expand=True)

        initials = "".join([w[0].upper() for w in goal.title.split()[:2]]) if goal.title else "??"
        if len(initials) > 2:
            initials = initials[:2]

        ctk.CTkLabel(
            placeholder,
            text=initials,
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _on_card_enter(self, card: ctk.CTkFrame, color: str) -> None:
        """Hover effect."""
        card.configure(border_color=color, border_width=2)

    def _on_card_leave(self, card: ctk.CTkFrame) -> None:
        """Reset hover."""
        card.configure(border_color="#E2E8F0", border_width=1)