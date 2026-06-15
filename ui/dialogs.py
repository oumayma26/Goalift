"""
ui/dialogs.py
Dialogues modaux - Thème CLAIR, couleur et image.
"""

import customtkinter as ctk
from tkinter import messagebox, colorchooser, filedialog
from typing import Optional, Callable
from models import Goal, Task
from services.goal_service import GoalService
from PIL import Image
import os

class GoalDialog(ctk.CTkToplevel):
    """Dialogue Goal avec couleur et image."""

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
        self.selected_color = goal.color if goal else "#3B82F6"
        self.selected_image_path = goal.image_path if goal else None
        self.temp_image_path = None
        self._current_image = None

        self.title("Modifier l'objectif" if self.is_edit else "Nouvel objectif")
        self.geometry("520x650")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        self._build_form()

        if self.is_edit:
            self._fill_form()

    def _build_form(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF", corner_radius=0)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            scroll_frame,
            text="Modifier l'objectif" if self.is_edit else "Nouvel objectif",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", pady=(0, 20))

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
            height=40,
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.title_entry.pack(fill="x", pady=(0, 15))

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
        self.desc_text.pack(fill="x", pady=(0, 15))

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
            height=40,
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.target_entry.pack(fill="x", pady=(0, 15))

        # ─── COULEUR ───
        ctk.CTkLabel(
            scroll_frame,
            text="🎨 Couleur",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 10))

        self.color_btn = ctk.CTkButton(
            scroll_frame,
            text="Choisir une couleur",
            height=40,
            corner_radius=8,
            fg_color=self.selected_color,
            hover_color=self.selected_color,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._choose_color
        )
        self.color_btn.pack(fill="x", pady=(0, 15))

        # ─── IMAGE ───
        ctk.CTkLabel(
            scroll_frame,
            text="🖼️ Image",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 10))

        # Frame pour l'image
        self.image_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color="#F8FAFC",
            corner_radius=12,
            height=150
        )
        self.image_frame.pack(fill="x", pady=(0, 5))
        self.image_frame.pack_propagate(False)

        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="Aucune image",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.image_label.pack(expand=True)

        # Boutons image
        img_btn_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        img_btn_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            img_btn_frame,
            text="📁 Choisir une image",
            height=35,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12),
            command=self._choose_image
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            img_btn_frame,
            text="🗑️ Supprimer",
            height=35,
            corner_radius=8,
            fg_color="#FEE2E2",
            hover_color="#FECACA",
            text_color="#DC2626",
            font=ctk.CTkFont(size=12),
            command=self._remove_image
        ).pack(side="left")

        # Priorité
        ctk.CTkLabel(
            scroll_frame,
            text="Priorité",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.priority_var = ctk.StringVar(value="Moyenne")
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
        priorities.pack(fill="x", pady=(0, 15))

        # Statut (édition)
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
                height=40,
                corner_radius=8,
                fg_color="#F8FAFC",
                button_color="#E2E8F0",
                text_color="#1E293B",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#1E293B",
                dropdown_hover_color="#F1F5F9",
                font=ctk.CTkFont(size=12)
            ).pack(fill="x", pady=(0, 15))

        # Boutons
        btn_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.grid_propagate(False)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkFrame(btn_frame, height=1, fg_color="#E2E8F0").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15)
        )

        ctk.CTkButton(
            btn_frame,
            text="Annuler",
            command=self.destroy,
            height=40,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="💾 Enregistrer",
            command=self._save,
            height=40,
            corner_radius=8,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=1, sticky="ew", padx=(8, 0))

    def _choose_color(self):
        color = colorchooser.askcolor(title="Choisir une couleur", color=self.selected_color)
        if color[1]:
            self.selected_color = color[1]
            self.color_btn.configure(fg_color=self.selected_color, hover_color=self.selected_color)

    def _choose_image(self):
        """Ouvre un sélecteur de fichier pour choisir une image."""
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Tous fichiers", "*.*")
        ]
        path = filedialog.askopenfilename(title="Choisir une image", filetypes=filetypes)
        if path:
            self.temp_image_path = path
            self._display_image(path)

    def _remove_image(self):
        """Supprime l'image sélectionnée."""
        self.temp_image_path = None
        self.selected_image_path = None
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="Aucune image",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.image_label.pack(expand=True)

    def _display_image(self, path: str):
        """Affiche l'image dans le frame."""
        try:
            for widget in self.image_frame.winfo_children():
                widget.destroy()

            img = Image.open(path)
            img.thumbnail((280, 130))

            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

            label = ctk.CTkLabel(self.image_frame, text="", image=ctk_image)
            label.pack(expand=True)

            self._current_image = ctk_image

        except Exception as e:
            self.image_label = ctk.CTkLabel(
                self.image_frame,
                text=f"Erreur: {str(e)}",
                font=ctk.CTkFont(size=11),
                text_color="#EF4444"
            )
            self.image_label.pack(expand=True)

    def _fill_form(self):
        if not self.goal:
            return

        self.title_entry.insert(0, self.goal.title)
        self.desc_text.insert("0.0", self.goal.description)
        if self.goal.target_date:
            self.target_entry.insert(0, self.goal.target_date.strftime("%Y-%m-%d"))
        self.priority_var.set(self.goal.priority)
        self.selected_color = self.goal.color
        self.color_btn.configure(fg_color=self.selected_color, hover_color=self.selected_color)

        if self.goal.image_path and os.path.exists(self.goal.image_path):
            self.selected_image_path = self.goal.image_path
            self._display_image(self.goal.image_path)

    def _save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return

        description = self.desc_text.get("0.0", "end").strip()
        target_date = self.target_entry.get().strip() or None
        priority = self.priority_var.get()
        color = self.selected_color

        try:
            if self.is_edit:
                final_image_path = self.selected_image_path
                if self.temp_image_path:
                    final_image_path = self.service.save_goal_image(self.goal.id, self.temp_image_path)
                    if self.goal.image_path and self.goal.image_path != final_image_path:
                        self.service.delete_goal_image(self.goal.image_path)

                status = self.status_var.get()
                self.service.update_goal(
                    self.goal.id,
                    title=title,
                    description=description,
                    target_date=target_date,
                    priority=priority,
                    status=status,
                    color=color,
                    image_path=final_image_path
                )
            else:
                new_goal = self.service.create_goal(
                    title=title,
                    description=description,
                    target_date=target_date,
                    priority=priority,
                    color=color,
                    image_path=None
                )

                final_image_path = None
                if self.temp_image_path:
                    final_image_path = self.service.save_goal_image(new_goal.id, self.temp_image_path)
                    self.service.update_goal(new_goal.id, image_path=final_image_path)

            if self.on_save:
                self.on_save()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erreur", str(e))


# ═══════════════════════════════════════════════════
# TASK DIALOG - CLASSE SÉPARÉE
# ═══════════════════════════════════════════════════

class TaskDialog(ctk.CTkToplevel):
    """Dialogue Task."""

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

    def _build_form(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF", corner_radius=0)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            scroll_frame,
            text="Modifier la tâche" if self.is_edit else "Nouvelle tâche",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(
            scroll_frame,
            text="Nom de la tâche *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#475569"
        ).pack(anchor="w", pady=(0, 5))

        self.name_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="Nom...",
            height=40,
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0",
            fg_color="#F8FAFC",
            text_color="#1E293B",
            font=ctk.CTkFont(size=12)
        )
        self.name_entry.pack(fill="x", pady=(0, 15))

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
        self.desc_text.pack(fill="x", pady=(0, 15))

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
                height=40,
                corner_radius=8,
                fg_color="#F8FAFC",
                button_color="#E2E8F0",
                text_color="#1E293B",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#1E293B",
                dropdown_hover_color="#F1F5F9",
                font=ctk.CTkFont(size=12)
            ).pack(fill="x", pady=(0, 15))

        btn_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.grid_propagate(False)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkFrame(btn_frame, height=1, fg_color="#E2E8F0").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15)
        )

        ctk.CTkButton(
            btn_frame,
            text="Annuler",
            command=self.destroy,
            height=40,
            corner_radius=8,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="💾 Enregistrer",
            command=self._save,
            height=40,
            corner_radius=8,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=1, sticky="ew", padx=(8, 0))

    def _fill_form(self):
        if not self.task:
            return
        self.name_entry.insert(0, self.task.name)
        self.desc_text.insert("0.0", self.task.description)

    def _save(self):
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