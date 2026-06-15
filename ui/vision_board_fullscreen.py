"""
ui/vision_board_fullscreen.py
Plein écran immersif du Vision Board - Rendu robuste des images.
"""

import os
import tkinter as tk
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont


@dataclass
class RenderedItem:
    """Garde les références pour éviter le garbage collection."""
    photo: ImageTk.PhotoImage
    shadow: Optional[ImageTk.PhotoImage] = None
    canvas_ids: list = None
    
    def __post_init__(self):
        if self.canvas_ids is None:
            self.canvas_ids = []


class VisionBoardFullscreen:
    """
    Plein écran du Vision Board - Images garanties visibles.
    """

    def __init__(
        self,
        master: ctk.CTk,
        items: Dict[int, 'VisionItem'],
        texts: Dict[int, 'FloatingText'],
        canvas_width: int = 2000,
        canvas_height: int = 1400,
        on_close: Optional[Callable] = None
    ):
        self.master = master
        self.items = items
        self.texts = texts
        self.canvas_w = canvas_width
        self.canvas_h = canvas_height
        self.on_close = on_close
        
        self._overlay: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None
        
        # CRUCIAL : Dictionnaire pour garder les références d'images
        self._image_refs: Dict[int, RenderedItem] = {}
        self._text_refs: Dict[int, ImageTk.PhotoImage] = {}

    def enter(self) -> None:
        """Entre en mode plein écran."""
        self._build_overlay()
        self._render_board()
        self._bind_controls()

    def exit(self) -> None:
        """Quitte le mode plein écran."""
        # Nettoyer les références
        self._image_refs.clear()
        self._text_refs.clear()
        
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None
        
        if self.on_close:
            self.on_close()

    def _build_overlay(self) -> None:
        """Construit la fenêtre plein écran."""
        self._overlay = tk.Toplevel(self.master)
        self._overlay.attributes("-fullscreen", True)
        self._overlay.configure(bg="#0F172A")
        self._overlay.overrideredirect(True)

        # Canvas qui prend tout l'écran
        self._canvas = tk.Canvas(
            self._overlay,
            bg="#0F172A",
            highlightthickness=0
        )
        self._canvas.pack(fill="both", expand=True)

        # Forcer le rendu pour avoir les vraies dimensions
        self._overlay.update_idletasks()
        self._overlay.update()

        # Bouton quitter
        self._exit_btn = ctk.CTkButton(
            self._overlay,
            text="✕  Quitter",
            width=100, height=36,
            corner_radius=20,
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#F8FAFC",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.exit
        )
        self._exit_btn.place(relx=0.98, rely=0.02, anchor="ne")

        # Label discret
        ctk.CTkLabel(
            self._overlay,
            text="✨ Vision Board",
            font=ctk.CTkFont(size=13),
            text_color="#475569",
            fg_color="transparent"
        ).place(relx=0.02, rely=0.02, anchor="nw")

    def _render_board(self) -> None:
        """Rend le Vision Board centré et scalé."""
        # Dimensions écran (après update_idletasks)
        screen_w = self._overlay.winfo_width()
        screen_h = self._overlay.winfo_height()
        
        if screen_w < 100 or screen_h < 100:
            # Fallback si les dimensions ne sont pas prêtes
            screen_w = self._overlay.winfo_screenwidth()
            screen_h = self._overlay.winfo_screenheight()

        # Scale : fit le board dans l'écran avec marge
        scale_x = (screen_w - 80) / self.canvas_w
        scale_y = (screen_h - 120) / self.canvas_h
        self._scale = min(scale_x, scale_y, 1.0)  # Max 1:1
        self._scale = max(self._scale, 0.3)  # Min 30%

        # Dimensions affichées
        display_w = int(self.canvas_w * self._scale)
        display_h = int(self.canvas_h * self._scale)

        # Offset pour centrer
        self._offset_x = (screen_w - display_w) // 2
        self._offset_y = (screen_h - display_h) // 2 + 20

        # Zone visible du board (clip rectangle)
        self._canvas.create_rectangle(
            self._offset_x - 1, self._offset_y - 1,
            self._offset_x + display_w + 1, self._offset_y + display_h + 1,
            outline="#334155", width=1, tags="board_border"
        )

        # Rendre les items (goals + mood)
        for item in self.items.values():
            self._render_item(item)

        # Rendre les textes
        for text in self.texts.values():
            self._render_text(text)

    def _render_item(self, item) -> None:
        """Rend un item avec ses images correctement référencées."""
        # Coordonnées scaled
        x = self._offset_x + int(item.x * self._scale)
        y = self._offset_y + int(item.y * self._scale)
        w = max(1, int(item.width * self._scale))
        h = max(1, int(item.height * self._scale))

        rendered = RenderedItem(photo=None)

        # 1. OMBRE (dessinée avant l'image)
        shadow = self._make_shadow(w, h)
        if shadow:
            shadow_id = self._canvas.create_image(
                x + 4, y + 4,
                image=shadow, anchor="nw"
            )
            rendered.shadow = shadow
            rendered.canvas_ids.append(shadow_id)

        # 2. IMAGE PRINCIPALE
        try:
            photo = self._make_card_image(item, w, h)
            if photo:
                img_id = self._canvas.create_image(
                    x, y,
                    image=photo, anchor="nw",
                    tags=f"item_{item.goal_id}"
                )
                rendered.photo = photo
                rendered.canvas_ids.append(img_id)
            else:
                # Fallback si l'image n'a pas pu être créée
                rect_id = self._canvas.create_rectangle(
                    x, y, x + w, y + h,
                    fill=item.color, outline="", width=0
                )
                rendered.canvas_ids.append(rect_id)
        except Exception as e:
            print(f"❌ Erreur rendu item {item.goal_id}: {e}")
            # Fallback rectangle
            rect_id = self._canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=item.color, outline="", width=0
            )
            rendered.canvas_ids.append(rect_id)

        # 3. BORDURE COLORÉE (par-dessus)
        border_id = self._canvas.create_rectangle(
            x - 1, y - 1, x + w + 1, y + h + 1,
            outline=item.color, width=2
        )
        rendered.canvas_ids.append(border_id)

        # 4. TITRE (si pas déjà dans l'image)
        if item.title and not item.image_path:
            text_id = self._canvas.create_text(
                x + w // 2, y + h // 2,
                text=item.title[:20],
                fill="#FFFFFF",
                font=("Segoe UI", max(10, int(14 * self._scale)), "bold"),
                anchor="center"
            )
            rendered.canvas_ids.append(text_id)

        # GARDER LA RÉFÉRENCE CRUCIALE
        self._image_refs[item.goal_id] = rendered

    def _render_text(self, text_obj) -> None:
        """Rend un texte flottant."""
        x = self._offset_x + int(text_obj.x * self._scale)
        y = self._offset_y + int(text_obj.y * self._scale)
        style = text_obj.style

        font_size = max(8, int(style.font_size * self._scale))

        # Background
        if style.background:
            padding = 6
            # Estimer la largeur du texte
            approx_width = len(text_obj.text) * font_size * 0.6
            approx_height = font_size * 1.5
            
            bg_id = self._canvas.create_rectangle(
                x - padding, y - padding,
                x + int(approx_width) + padding, y + int(approx_height) + padding,
                fill=style.background,
                outline="", width=0,
                stipple="gray50" if style.opacity < 200 else ""
            )

        # Texte
        text_id = self._canvas.create_text(
            x, y,
            text=text_obj.text,
            fill=style.color,
            font=(style.font_family, font_size, 
                  "bold" if style.bold else "normal",
                  "italic" if style.italic else "roman"),
            anchor="nw"
        )

    def _make_shadow(self, w: int, h: int) -> Optional[ImageTk.PhotoImage]:
        """Crée une ombre subtile."""
        try:
            pad = 8
            img = Image.new("RGBA", (w + pad, h + pad), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            for i in range(3):
                alpha = 20 - i * 5
                offset = 2 + i
                draw.rounded_rectangle(
                    (offset, offset, offset + w, offset + h),
                    radius=6, fill=(0, 0, 0, alpha)
                )
            
            # Fond correspondant à la couleur du canvas
            final = Image.new("RGB", img.size, (15, 23, 42))
            final.paste(img, mask=img.split()[3])
            return ImageTk.PhotoImage(final)
        except Exception as e:
            print(f"⚠️ Erreur ombre: {e}")
            return None

    def _make_card_image(self, item, w: int, h: int) -> Optional[ImageTk.PhotoImage]:
        """
        Crée l'image d'une card. 
        Gère les erreurs de fichier et retourne None si impossible.
        """
        # Vérifier que le fichier existe
        if not item.image_path or not os.path.exists(item.image_path):
            return None

        try:
            # Charger l'image
            img = Image.open(item.image_path).convert("RGB")
            
            # Crop center pour le ratio cible
            img = self._crop_center(img, w, h)
            img = img.resize((w, h), Image.Resampling.LANCZOS)

            # Overlay dégradé pour le titre
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Dégradé subtil en bas
            for i in range(35):
                alpha = int(100 * (i / 35))
                draw.rectangle((0, h - 35 + i, w, h - 35 + i + 1), 
                              fill=(0, 0, 0, alpha))

            # Titre
            if item.title:
                try:
                    font_size = max(8, int(12 * self._scale))
                    font = ImageFont.truetype("segoeui.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), item.title, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                
                # Tronquer si trop long
                display_title = item.title
                while tw > w - 20 and len(display_title) > 3:
                    display_title = display_title[:-2] + "…"
                    bbox = draw.textbbox((0, 0), display_title, font=font)
                    tw = bbox[2] - bbox[0]

                draw.text(((w - tw) // 2, h - th - 8), 
                         display_title, fill="#FFFFFF", font=font)

            # Combiner
            rgba = img.convert("RGBA")
            result = Image.alpha_composite(rgba, overlay)
            result = self._round_corners(result, 8)

            # Fond pour les zones transparentes (coins arrondis)
            final = Image.new("RGB", result.size, (15, 23, 42))
            final.paste(result, mask=result.split()[3])

            # CRUCIAL : Garder la référence
            photo = ImageTk.PhotoImage(final)
            return photo

        except Exception as e:
            print(f"⚠️ Erreur création image pour '{item.title}': {e}")
            return None

    def _crop_center(self, img: Image.Image, tw: int, th: int) -> Image.Image:
        """Recadre l'image au centre pour le ratio cible."""
        w, h = img.size
        if w == 0 or h == 0:
            return img
        
        ratio = tw / th if th > 0 else 1.0
        curr = w / h
        
        if curr > ratio:
            new_w = int(h * ratio)
            left = (w - new_w) // 2
            return img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / ratio)
            top = (h - new_h) // 2
            return img.crop((0, top, w, top + new_h))

    def _round_corners(self, img: Image.Image, r: int) -> Image.Image:
        """Arrondit les coins."""
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=r, fill=255)
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.paste(img, (0, 0))
        out.putalpha(mask)
        return out

    def _bind_controls(self) -> None:
        """Bind les contrôles."""
        self._overlay.bind("<Escape>", lambda e: self.exit())
        self._overlay.bind("<F11>", lambda e: self.exit())
        self._overlay.bind("<KeyPress-q>", lambda e: self.exit())
        self._overlay.bind("<Button-3>", lambda e: self.exit())  # Clic droit = quitter
        
        # Clic sur le fond = quitter (si pas sur un item)
        self._canvas.bind("<Button-1>", self._on_canvas_click)

    def _on_canvas_click(self, event):
        """Quitte si clic sur le fond vide."""
        items = self._canvas.find_closest(event.x, event.y)
        if items:
            # Vérifier si c'est un item ou le fond
            tags = self._canvas.gettags(items[0])
            if not tags or not any(t.startswith("item_") or t.startswith("text_") for t in tags):
                self.exit()
        else:
            self.exit()