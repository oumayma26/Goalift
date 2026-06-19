"""
ui/wird_view.py
Vue Wird — Interface de gestion et d'exécution des programmes spirituels.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, List
from services.wird_service import WirdService
from database.database import DatabaseManager


class WirdListView(ctk.CTkFrame):
    """Liste des Wirds avec quick actions."""
    
    def __init__(self, parent, db: DatabaseManager, on_start_session: Callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db
        self.service = WirdService(db)
        self.on_start_session = on_start_session
        
        self._build_header()
        self._build_wird_list()
    
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="📿 Mes Wirds",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="➕ Nouveau Wird",
            command=self._create_new_wird,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        ).pack(side="right")
    
    def _create_new_wird(self):
        """Ouvre le dialogue de création de Wird."""
        dialog = WirdDialog(self, db=self.db, on_save=self._refresh_list)
        dialog.grab_set()

    def _refresh_list(self):
        """Recharge la liste des Wirds."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build_header()
        self._build_wird_list()
    
    def _build_wird_list(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        wirds = self.service.get_active_wirds()
        
        if not wirds:
            ctk.CTkLabel(
                scroll,
                text="Aucun Wird créé. Cliquez sur ➕ pour commencer.",
                font=ctk.CTkFont(size=14),
                text_color="#94A3B8"
            ).pack(pady=40)
            return
        
        for wird in wirds:
            self._create_wird_card(scroll, wird)
    
    def _create_wird_card(self, parent, wird: dict):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16, height=120)
        card.pack(fill="x", pady=8, padx=5)
        card.pack_propagate(False)
        
        # Indicateur de couleur
        indicator = ctk.CTkFrame(card, width=4, fg_color=wird["color"], corner_radius=2)
        indicator.pack(side="left", fill="y", padx=0, pady=0)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        # Header
        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x")
        
        ctk.CTkLabel(
            top,
            text=f"{wird['icon']} {wird['title']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")
        
        # Badge "Dû aujourd'hui"
        if wird["is_due_today"]:
            badge = ctk.CTkFrame(top, fg_color="#FEF3C7", corner_radius=6, height=24)
            badge.pack(side="right", padx=5)
            ctk.CTkLabel(
                badge,
                text="Aujourd'hui",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#D97706"
            ).pack(padx=8, pady=2)
        
        # Stats
        stats = ctk.CTkFrame(content, fg_color="transparent")
        stats.pack(fill="x", pady=(8, 0))
        
        streak = wird["stats"]["current_streak"]
        ctk.CTkLabel(
            stats,
            text=f"🔥 Streak: {streak} jours" if streak > 0 else "Pas encore commencé",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).pack(side="left")
        
        rate = wird["stats"]["completion_rate"]
        ctk.CTkLabel(
            stats,
            text=f"{rate}% cette semaine",
            font=ctk.CTkFont(size=12),
            text_color="#10B981" if rate >= 80 else "#64748B"
        ).pack(side="right")
        
        # Bouton d'action
        btn_text = "▶️ Commencer" if wird["is_due_today"] else "📊 Voir stats"
        btn_color = wird["color"] if wird["is_due_today"] else "#E2E8F0"
        btn_text_color = "#FFFFFF" if wird["is_due_today"] else "#64748B"
        
        btn = ctk.CTkButton(
            card,
            text=btn_text,
            width=120,
            height=36,
            corner_radius=10,
            fg_color=btn_color,
            hover_color=btn_color,
            text_color=btn_text_color,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda w=wird: self.on_start_session(w["id"])
        )
        btn.pack(side="right", padx=15, pady=12)


class WirdDialog(ctk.CTkToplevel):
    """Dialogue de création/édition d'un Wird."""
    
    def __init__(self, parent, db: DatabaseManager, on_save: Callable = None, edit_wird_id: Optional[int] = None):
        super().__init__(parent)
        
        self.db = db
        self.on_save = on_save
        self.edit_wird_id = edit_wird_id
        
        self.title("Nouveau Wird" if not edit_wird_id else "Modifier Wird")
        self.geometry("520x700")  # ← PLUS GRAND
        self.resizable(False, False)
        
        self.items = []
        
        self._build_form()
    
    def _build_form(self):
        # Titre
        ctk.CTkLabel(
            self,
            text="📿 Nouveau Wird",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(pady=(15, 10))
        
        # === FORMULAIRE (scrollable si trop long) ===
        form = ctk.CTkScrollableFrame(self, fg_color="transparent", height=520)
        form.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Nom
        ctk.CTkLabel(form, text="Nom", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").pack(anchor="w")
        self.title_entry = ctk.CTkEntry(form, placeholder_text="Ex: Wird du Matin")
        self.title_entry.pack(fill="x", pady=(5, 12))
        
        # Description
        ctk.CTkLabel(form, text="Description", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").pack(anchor="w")
        self.desc_entry = ctk.CTkEntry(form, placeholder_text="Optionnel")
        self.desc_entry.pack(fill="x", pady=(5, 12))
        
        # Schedule
        ctk.CTkLabel(form, text="Fréquence", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B").pack(anchor="w")
        self.schedule_var = ctk.StringVar(value="daily")
        self.schedule_menu = ctk.CTkOptionMenu(
            form,
            values=["daily", "fajr", "dhuhr", "asr", "maghrib", "isha", "custom"],
            variable=self.schedule_var
        )
        self.schedule_menu.pack(fill="x", pady=(5, 12))
        
        # Items
        ctk.CTkLabel(form, text="Items", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1E293B").pack(anchor="w", pady=(10, 5))
        
        self.items_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.items_frame.pack(fill="x", pady=5)
        
        # Bouton ajouter item
        ctk.CTkButton(
            form,
            text="➕ Ajouter un item",
            command=self._add_item_row,
            fg_color="#E2E8F0",
            hover_color="#CBD5E1",
            text_color="#64748B",
            height=32
        ).pack(fill="x", pady=(5, 10))
        
        # === BOUTONS FIXES EN BAS ===
        btns = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btns.pack(fill="x", padx=20, pady=(5, 15))
        btns.pack_propagate(False)
        
        ctk.CTkButton(
            btns,
            text="❌ Annuler",
            command=self.destroy,
            fg_color="#E2E8F0",
            hover_color="#CBD5E1",
            text_color="#64748B",
            width=120,
            height=40,
            corner_radius=10
        ).pack(side="left")
        
        ctk.CTkButton(
            btns,
            text="✅ Créer le Wird",
            command=self._save,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            width=180,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="right")
        
        # Item par défaut
        self._add_item_row()
    
    def _add_item_row(self):
        row = ctk.CTkFrame(self.items_frame, fg_color="#F1F5F9", corner_radius=8)
        row.pack(fill="x", pady=3)
        
        title = ctk.CTkEntry(row, placeholder_text="Titre", width=180)
        title.pack(side="left", padx=5, pady=5)
        
        count = ctk.CTkEntry(row, placeholder_text="1", width=45)
        count.pack(side="left", padx=5, pady=5)
        count.insert(0, "1")
        
        unit = ctk.CTkOptionMenu(row, values=["fois", "minutes", "pages", "versets"], width=90)
        unit.pack(side="left", padx=5, pady=5)
        
        icon = ctk.CTkEntry(row, placeholder_text="✨", width=40)
        icon.pack(side="left", padx=5, pady=5)
        icon.insert(0, "✨")
        
        # Bouton supprimer
        del_btn = ctk.CTkButton(
            row,
            text="🗑",
            width=30,
            height=28,
            fg_color="#FEE2E2",
            hover_color="#FECACA",
            text_color="#EF4444",
            command=lambda r=row: self._remove_item_row(r)
        )
        del_btn.pack(side="right", padx=5, pady=5)
        
        self.items.append({
            "frame": row,
            "title": title,
            "count": count,
            "unit": unit,
            "icon": icon
        })
    
    def _remove_item_row(self, row_frame):
        """Supprime un item de la liste."""
        for item in self.items:
            if item["frame"] == row_frame:
                self.items.remove(item)
                row_frame.destroy()
                break
    
    def _save(self):
        title = self.title_entry.get().strip()
        if not title:
            # Feedback visuel
            self.title_entry.configure(border_color="#EF4444")
            self.after(1000, lambda: self.title_entry.configure(border_color="#E2E8F0"))
            return
        
        desc = self.desc_entry.get().strip() or None
        schedule = self.schedule_var.get()
        
        # Créer le Wird
        wird_id = self.db.create_wird(
            title=title,
            description=desc,
            schedule_type=schedule
        )
        
        # Ajouter les items
        for idx, item in enumerate(self.items):
            t = item["title"].get().strip()
            if not t:
                continue
            try:
                c = int(item["count"].get() or 1)
            except ValueError:
                c = 1
            u = item["unit"].get()
            i = item["icon"].get() or "✨"
            
            self.db.add_wird_item(
                wird_id=wird_id,
                title=t,
                target_count=c,
                unit=u,
                icon=i,
                order_index=idx
            )
        
        if self.on_save:
            self.on_save()
        
        self.destroy()

class WirdSessionView(ctk.CTkFrame):
    """Vue d'exécution d'une session Wird (mode focus)."""
    
    def __init__(self, parent, db: DatabaseManager, wird_id: int, on_finish: Callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db
        self.service = WirdService(db)
        self.wird_id = wird_id
        self.on_finish = on_finish
        
        self.session = self.service.start_session(wird_id)
        self.current_item_idx = 0
        
        self._build_ui()
        self._show_current_item()
    
    def _build_ui(self):
        # Header avec progression
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.header.pack(fill="x", padx=30, pady=20)
        
        self.progress_label = ctk.CTkLabel(
            self.header,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#64748B"
        )
        self.progress_label.pack(side="left")
        
        # Timer
        self.timer_label = ctk.CTkLabel(
            self.header,
            text="00:00",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3B82F6"
        )
        self.timer_label.pack(side="right")
        
        # Zone principale (item en cours)
        self.main_zone = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=20)
        self.main_zone.pack(fill="both", expand=True, padx=30, pady=20)
        
        self.item_icon = ctk.CTkLabel(self.main_zone, text="", font=ctk.CTkFont(size=48))
        self.item_icon.pack(pady=(40, 10))
        
        self.item_title = ctk.CTkLabel(
            self.main_zone,
            text="",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#1E293B"
        )
        self.item_title.pack(pady=10)
        
        self.item_desc = ctk.CTkLabel(
            self.main_zone,
            text="",
            font=ctk.CTkFont(size=16),
            text_color="#64748B"
        )
        self.item_desc.pack(pady=5)
        
        # Compteur
        self.counter_frame = ctk.CTkFrame(self.main_zone, fg_color="transparent")
        self.counter_frame.pack(pady=20)
        
        self.counter = ctk.CTkLabel(
            self.counter_frame,
            text="0 / 0",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#3B82F6"
        )
        self.counter.pack()
        
        # Boutons d'action
        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.pack(fill="x", padx=30, pady=20)
        
        self.skip_btn = ctk.CTkButton(
            self.actions,
            text="⏭ Passer",
            command=self._skip_item,
            fg_color="#E2E8F0",
            hover_color="#CBD5E1",
            text_color="#64748B",
            height=50,
            corner_radius=12
        )
        self.skip_btn.pack(side="left", expand=True, padx=5)
        
        self.complete_btn = ctk.CTkButton(
            self.actions,
            text="✅ Terminé",
            command=self._complete_item,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            height=50,
            corner_radius=12,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.complete_btn.pack(side="right", expand=True, padx=5)
    
    def _show_current_item(self):
        items = self.session["items"]
        if self.current_item_idx >= len(items):
            self._finish_session()
            return
            
        item = items[self.current_item_idx]
        self.item_icon.configure(text=item["icon"])
        self.item_title.configure(text=item["title"])
        self.item_desc.configure(text=f"{item['target_count']} {item['unit']}")
        self.counter.configure(text=f"0 / {item['target_count']}")
        
        completed = self.session["completed_count"]
        total = len(items)
        self.progress_label.configure(text=f"Étape {self.current_item_idx + 1} / {total}  •  {completed} terminés")
        
        # Masquer "Passer" si obligatoire
        if not item["is_optional"]:
            self.skip_btn.pack_forget()
        else:
            self.skip_btn.pack(side="left", expand=True, padx=5)
    
    def _complete_item(self):
        items = self.session["items"]
        item = items[self.current_item_idx]
        
        self.service.complete_item(
            self.session["session"]["id"],
            item["id"],
            count=item["target_count"]
        )
        
        self.current_item_idx += 1
        self._refresh_session()
        self._show_current_item()
    
    def _skip_item(self):
        items = self.session["items"]
        item = items[self.current_item_idx]
        self.service.skip_item(self.session["session"]["id"], item["id"])
        self.current_item_idx += 1
        self._refresh_session()
        self._show_current_item()
    
    def _refresh_session(self):
        self.session = self.db.get_wird_session_progress(self.session["session"]["id"])
    
    def _finish_session(self):
        # Écran de fin
        for widget in self.winfo_children():
            widget.destroy()
        
        self.configure(fg_color="#F0FDF4")
        
        ctk.CTkLabel(
            self,
            text="🎉 Masha'Allah !",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#059669"
        ).pack(pady=(60, 10))
        
        ctk.CTkLabel(
            self,
            text="Wird complété avec succès",
            font=ctk.CTkFont(size=18),
            text_color="#64748B"
        ).pack(pady=10)
        
        # Mood selector
        ctk.CTkLabel(
            self,
            text="Comment te sens-tu ?",
            font=ctk.CTkFont(size=14),
            text_color="#64748B"
        ).pack(pady=(30, 10))
        
        mood_frame = ctk.CTkFrame(self, fg_color="transparent")
        mood_frame.pack(pady=10)
        
        self.selected_mood = ctk.IntVar(value=3)
        for i in range(1, 6):
            btn = ctk.CTkButton(
                mood_frame,
                text="⭐" * i,
                width=60,
                height=40,
                corner_radius=8,
                fg_color="#FEF3C7" if i == 3 else "transparent",
                hover_color="#FEF3C7",
                text_color="#D97706",
                command=lambda m=i: self._select_mood(m)
            )
            btn.pack(side="left", padx=5)
        
        ctk.CTkButton(
            self,
            text="Terminer",
            command=self._finalize,
            fg_color="#059669",
            hover_color="#047857",
            height=50,
            width=200,
            corner_radius=12,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=40)
    
    def _select_mood(self, mood: int):
        self.selected_mood.set(mood)
    
    def _finalize(self):
        result = self.service.finish_session(
            self.session["session"]["id"],
            mood=self.selected_mood.get()
        )
        self.on_finish(result)