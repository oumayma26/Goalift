"""
ui/vision_board/canvas_renderer.py
Moteur de rendu PIL → Canvas Tkinter.
Responsabilité unique : dessiner des items sur un canvas.
"""

import os
import sys
import tkinter as tk
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageTk, ImageFont

from .constants import ARABIC_FONT_PATH, CANVAS_WIDTH, CANVAS_HEIGHT, COLORS
from models import VisionItem, FloatingText, TextStyle


# Vérifier si arabic_reshaper est disponible
_ARABIC_RESHAPER_AVAILABLE = False
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    pass


class CanvasRenderer:
    """
    Rendu d'images PIL sur un canvas Tkinter.
    Gère les ombres, coins arrondis, textes arabes, overlays.
    """

    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        # Cache pour éviter le garbage collection des images
        self._image_cache: Dict[int, ImageTk.PhotoImage] = {}

    # ═══════════════════════════════════════════════════
    # RENDU D'ITEM (goal ou mood)
    # ═══════════════════════════════════════════════════

    def draw_item(self, item: VisionItem) -> None:
        """Dessine un VisionItem complet (ombre + image + bordure)."""
        w, h = int(item.width), int(item.height)

        # 1. Ombre
        shadow = self._make_shadow(w, h)
        item.shadow_id = self.canvas.create_image(
            item.x + 5, item.y + 5, image=shadow, anchor="nw"
        )
        self._image_cache[f"shadow_{item.goal_id}"] = shadow

        # 2. Image principale
        img = self._make_card_image(item)
        item.tk_image = img
        item.canvas_id = self.canvas.create_image(
            item.x, item.y, image=img, anchor="nw"
        )
        self._image_cache[f"img_{item.goal_id}"] = img

        # 3. Bordure (cachée par défaut)
        self.canvas.create_rectangle(
            item.x - 2, item.y - 2,
            item.x + w + 2, item.y + h + 2,
            outline=item.color, width=2,
            state="hidden", tags=f"border_{item.goal_id}"
        )

        # 4. Handles de redimensionnement (cachés par défaut)
        self._draw_resize_handles(item)
        self.canvas.tag_raise(item.canvas_id)

    def redraw_item(self, item: VisionItem) -> None:
        """Redessine un item après redimensionnement."""
        self.clear_item(item)
        self.draw_item(item)
        self.show_resize_handles(item)

    def clear_item(self, item: VisionItem) -> None:
        """Supprime un item du canvas."""
        for tag in [item.canvas_id, item.shadow_id]:
            if tag:
                self.canvas.delete(tag)
        if hasattr(item, "resize_handles"):
            for hid in item.resize_handles:
                self.canvas.delete(hid)
        self.canvas.delete(f"border_{item.goal_id}")

        # Nettoyer cache
        self._image_cache.pop(f"shadow_{item.goal_id}", None)
        self._image_cache.pop(f"img_{item.goal_id}", None)

    def move_item(self, item: VisionItem, dx: float, dy: float) -> None:
        """Déplace un item de (dx, dy)."""
        for tag in [item.shadow_id, item.canvas_id]:
            if tag:
                self.canvas.move(tag, dx, dy)
        self.canvas.move(f"border_{item.goal_id}", dx, dy)
        if hasattr(item, "resize_handles"):
            for hid in item.resize_handles:
                self.canvas.move(hid, dx, dy)

    # ═══════════════════════════════════════════════════
    # RENDU DE TEXTE FLOTTANT
    # ═══════════════════════════════════════════════════

    def draw_text(self, text_obj: FloatingText) -> None:
        """Dessine un texte flottant."""
        img = self._render_text_image(text_obj)
        text_obj.tk_image = img

        if text_obj.canvas_id:
            self.canvas.delete(text_obj.canvas_id)
        if text_obj.bg_id:
            self.canvas.delete(text_obj.bg_id)

        text_obj.canvas_id = self.canvas.create_image(
            text_obj.x, text_obj.y,
            image=img, anchor="nw",
            tags=f"text_{text_obj.id}"
        )
        self._image_cache[f"text_{text_obj.id}"] = img

        bbox = self.canvas.bbox(text_obj.canvas_id)
        if bbox:
            text_obj.bg_id = self.canvas.create_rectangle(
                bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2,
                outline=COLORS["primary"], width=2,
                state="hidden", tags=f"text_border_{text_obj.id}"
            )

    def move_text(self, text_obj: FloatingText, dx: float, dy: float) -> None:
        """Déplace un texte."""
        self.canvas.move(text_obj.canvas_id, dx, dy)
        if text_obj.bg_id:
            self.canvas.move(text_obj.bg_id, dx, dy)

    def clear_text(self, text_obj: FloatingText) -> None:
        """Supprime un texte du canvas."""
        if text_obj.canvas_id:
            self.canvas.delete(text_obj.canvas_id)
        if text_obj.bg_id:
            self.canvas.delete(text_obj.bg_id)
        self._image_cache.pop(f"text_{text_obj.id}", None)

    # ═══════════════════════════════════════════════════
    # VISUALISATION DE SÉLECTION
    # ═══════════════════════════════════════════════════

    def show_border(self, item: VisionItem) -> None:
        """Affiche la bordure de sélection."""
        self.canvas.itemconfig(f"border_{item.goal_id}", state="normal")
        self.canvas.tag_raise(item.canvas_id)

    def hide_border(self, item: VisionItem) -> None:
        """Cache la bordure de sélection."""
        self.canvas.itemconfig(f"border_{item.goal_id}", state="hidden")

    def show_text_border(self, text_obj: FloatingText) -> None:
        """Affiche la bordure d'un texte."""
        if text_obj.bg_id:
            self.canvas.itemconfig(text_obj.bg_id, state="normal")

    def hide_text_border(self, text_obj: FloatingText) -> None:
        """Cache la bordure d'un texte."""
        if text_obj.bg_id:
            self.canvas.itemconfig(text_obj.bg_id, state="hidden")

    def show_resize_handles(self, item: VisionItem) -> None:
        """Affiche les handles de redimensionnement."""
        if hasattr(item, "resize_handles"):
            for hid in item.resize_handles:
                self.canvas.itemconfig(hid, state="normal")

    def hide_resize_handles(self, item: VisionItem) -> None:
        """Cache les handles de redimensionnement."""
        if hasattr(item, "resize_handles"):
            for hid in item.resize_handles:
                self.canvas.itemconfig(hid, state="hidden")

    # ═══════════════════════════════════════════════════
    # FABRICATION DES IMAGES PIL
    # ═══════════════════════════════════════════════════

    def _make_card_image(self, item: VisionItem) -> ImageTk.PhotoImage:
        """Crée l'image d'une card avec effets."""
        w, h = int(item.width), int(item.height)

        try:
            img = Image.open(item.image_path).convert("RGB")
        except Exception:
            img = Image.new("RGB", (w, h), self._hex_to_rgb(item.color))

        img = self._crop_center(img, w, h)
        img = img.resize((w, h), Image.Resampling.LANCZOS)

        if item.rotation != 0 and item.is_mood_item:
            img = img.rotate(item.rotation, expand=True, resample=Image.Resampling.BICUBIC)
            new_w, new_h = img.size
            if new_w > w or new_h > h:
                left = (new_w - w) // 2
                top = (new_h - h) // 2
                img = img.crop((left, top, left + w, top + h))

        # Overlay dégradé
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for i in range(50):
            alpha = int(140 * (i / 50))
            draw.rectangle((0, h - 50 + i, w, h - 50 + i + 1), fill=(0, 0, 0, alpha))

        # Titre
        font = self._get_font("segoeui.ttf", 13) or self._get_font("arial.ttf", 13)
        if item.title and font:
            bbox = draw.textbbox((0, 0), item.title, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((w - tw) // 2, h - 30), item.title, fill="#FFFFFF", font=font)

        rgba = img.convert("RGBA")
        result = Image.alpha_composite(rgba, overlay)
        result = self._round_corners(result, 10)

        final = Image.new("RGB", result.size, (255, 255, 255))
        final.paste(result, mask=result.split()[3])

        return ImageTk.PhotoImage(final)

    def _make_shadow(self, w: int, h: int) -> ImageTk.PhotoImage:
        """Crée une ombre subtile."""
        pad = 14
        img = Image.new("RGBA", (w + pad, h + pad), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for i in range(6):
            alpha = 20 - i * 3
            offset = 3 + i
            draw.rounded_rectangle(
                (offset, offset + 1, offset + w, offset + h + 1),
                radius=10, fill=(0, 0, 0, alpha)
            )
        final = Image.new("RGB", img.size, (250, 250, 250))
        final.paste(img, mask=img.split()[3])
        return ImageTk.PhotoImage(final)

    def _render_text_image(self, text_obj: FloatingText) -> ImageTk.PhotoImage:
        """Rend un texte en image avec support arabe (RTL + ligatures)."""
        style = text_obj.style
        text = text_obj.text

        # Détection arabe
        is_arabic = any(
            "\u0600" <= c <= "\u06FF" or "\u0750" <= c <= "\u077F" or "\u08A0" <= c <= "\u08FF" or
            "\uFB50" <= c <= "\uFDFF" or "\uFE70" <= c <= "\uFEFF"
            for c in text
        )

        # Choix police
        font = self._resolve_font(style, is_arabic)

        # ═══════════════════════════════════════════════════
        # ARABE : Reshape + BIDI ligne par ligne APRÈS le wrap
        # ═══════════════════════════════════════════════════
        MAX_WIDTH = 800 if is_arabic else 600

        if is_arabic:
            # 1. Wrap sur le texte original (logique)
            raw_lines = self._wrap_text(text, font, MAX_WIDTH)

            # 2. Reshape + BIDI chaque ligne séparément
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
                lines = []
                for line in raw_lines:
                    reshaped = arabic_reshaper.reshape(line)
                    bidi_line = get_display(reshaped)
                    lines.append(bidi_line)
            except Exception:
                lines = raw_lines
        else:
            lines = self._wrap_text(text, font, MAX_WIDTH)

        # Mesure
        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)
        max_w = 0
        total_h = 0
        line_heights = []

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            max_w = max(max_w, lw)
            line_heights.append(lh)
            total_h += lh + 12

        total_h += 24
        max_w += 60 if is_arabic else 40

        # Création image
        img = Image.new("RGBA", (max_w, total_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background
        if style.background and style.opacity > 0:
            r, g, b = self._hex_to_rgb(style.background)
            draw.rounded_rectangle(
                (0, 0, max_w, total_h), radius=12,
                fill=(r, g, b, style.opacity)
            )

        # Dessin
        y = 14
        for i, line in enumerate(lines):
            lh = line_heights[i]
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            
            if is_arabic:
                x = max_w - lw - 20
            else:
                x = (max_w - lw) // 2
            
            draw.text((x, y), line, fill=style.color, font=font)
            y += lh + 12

        return ImageTk.PhotoImage(img)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """Wrap LTR standard."""
        words = text.split()
        lines = []
        current_line = []
        
        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines if lines else [text]

    def _wrap_text_arabic(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """
        Wrap pour texte arabe NON reshapé.
        On split sur les espaces du texte logique (original).
        """
        words = text.split()
        lines = []
        current_line = []
        
        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        for word in words:
            test_line = " ".join(current_line + [word])
            # Pour mesurer, on doit reshape+BIDI le test_line
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
                reshaped = arabic_reshaper.reshape(test_line)
                display_text = get_display(reshaped)
            except:
                display_text = test_line
            
            bbox = draw.textbbox((0, 0), display_text, font=font)
            w = bbox[2] - bbox[0]
            
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines if lines else [text]

    def _wrap_text_rtl(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """
        Wrap pour texte arabe DÉJÀ reshapé + BIDI.
        Le texte est visuellement LTR après BIDI, donc wrap standard.
        """
        words = text.split()
        lines = []
        current_line = []
        
        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        for word in words:
            test_line = " ".join(current_line + [word])
            w = draw.textbbox((0, 0), test_line, font=font)[2]
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines if lines else [text]

    # ═══════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════

    def _draw_resize_handles(self, item: VisionItem) -> None:
        """Dessine les handles de redimensionnement."""
        w, h = item.width, item.height
        handle_size = 8
        handles = [(item.x + w, item.y + h, "se")]

        item.resize_handles = []
        for hx, hy, direction in handles:
            hid = self.canvas.create_rectangle(
                hx - handle_size // 2, hy - handle_size // 2,
                hx + handle_size // 2, hy + handle_size // 2,
                fill=COLORS["primary"], outline="#FFFFFF", width=2,
                tags=f"resize_handle_{item.goal_id}_{direction}",
                state="hidden"
            )
            item.resize_handles.append(hid)

    def _resolve_font(self, style: TextStyle, is_arabic: bool) -> ImageFont.FreeTypeFont:
        """Résout la police appropriée."""
        if is_arabic:
            # Essayer style.font_family (chemin vers .ttf)
            if style.font_family and os.path.exists(style.font_family):
                try:
                    size = max(style.font_size, 28)
                    return ImageFont.truetype(style.font_family, size)
                except Exception:
                    pass

            # Essayer ARABIC_FONT_PATH
            if os.path.exists(ARABIC_FONT_PATH):
                try:
                    size = max(style.font_size, 28)
                    return ImageFont.truetype(ARABIC_FONT_PATH, size)
                except Exception:
                    pass

            # Fallbacks système
            arabic_fonts = [
                ("ScheherazadeNew-Regular.ttf", 32),
                ("Scheherazade-Regular.ttf", 32),
                ("Amiri-Regular.ttf", 28),
                ("arial.ttf", 24),
                ("segoeui.ttf", 24),
                ("tahoma.ttf", 22),
            ]
            for name, size in arabic_fonts:
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    continue

            return ImageFont.load_default()

        # Texte latin (inchangé)
        try:
            if os.path.exists(style.font_family):
                return ImageFont.truetype(style.font_family, style.font_size)
            return ImageFont.truetype(f"{style.font_family}.ttf", style.font_size)
        except Exception:
            try:
                return ImageFont.truetype("arial.ttf", style.font_size)
            except Exception:
                return ImageFont.load_default()
            
    def _get_font(self, name: str, size: int) -> Optional[ImageFont.FreeTypeFont]:
        """Charge une police système."""
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            return None

    def _crop_center(self, img: Image.Image, tw: int, th: int) -> Image.Image:
        """Recadre l'image au centre pour le ratio cible."""
        w, h = img.size
        ratio = tw / th
        curr = w / h
        if curr > ratio:
            nw = int(h * ratio)
            left = (w - nw) // 2
            return img.crop((left, 0, left + nw, h))
        else:
            nh = int(w / ratio)
            top = (h - nh) // 2
            return img.crop((0, top, w, top + nh))

    def _round_corners(self, img: Image.Image, r: int) -> Image.Image:
        """Arrondit les coins."""
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=r, fill=255)
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.paste(img, (0, 0))
        out.putalpha(mask)
        return out

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convertit un hex en RGB."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))