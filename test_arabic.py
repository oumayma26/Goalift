"""
test_no_bidi.py
Test sans BIDI, juste alignement droite.
"""

import os
from PIL import Image, ImageDraw, ImageFont

TEST_TEXT = "إِنَّ مَعَ الْعُسْرِ يُسْرًا"

font = ImageFont.truetype("assets/fonts/ScheherazadeNew-Medium.ttf", 32)

# Test 1 : Texte brut, aligné à droite, une ligne
img1 = Image.new("RGBA", (600, 80), (255, 255, 255, 255))
draw1 = ImageDraw.Draw(img1)
bbox = draw1.textbbox((0, 0), TEST_TEXT, font=font)
w = bbox[2] - bbox[0]
draw1.text((580 - w, 20), TEST_TEXT, fill="#059669", font=font)
img1.save("test_no_bidi_1.png")
print("1. Brut, aligné droite - sauvegardé")

# Test 2 : Wrap manuel, lignes inversées
words = TEST_TEXT.split()
# Inverser l'ordre des mots pour le wrap
words_inv = list(reversed(words))
print(f"Mots inversés: {words_inv}")

# Wrap LTR sur mots inversés
lines = []
current = []
max_w = 300
dummy = Image.new("RGBA", (1, 1))
draw = ImageDraw.Draw(dummy)

for word in words_inv:
    test = " ".join(current + [word])
    w = draw.textbbox((0, 0), test, font=font)[2]
    if w <= max_w:
        current.append(word)
    else:
        if current:
            lines.append(" ".join(current))
        current = [word]
if current:
    lines.append(" ".join(current))

# Re-inverser chaque ligne et l'ordre des lignes
result = []
for line in reversed(lines):
    words_line = line.split()
    result.append(" ".join(reversed(words_line)))

print(f"Lignes résultat: {result}")

# Dessiner
img2 = Image.new("RGBA", (400, 150), (255, 255, 255, 255))
draw2 = ImageDraw.Draw(img2)
y = 20
for line in result:
    bbox = draw2.textbbox((0, 0), line, font=font)
    w = bbox[2] - bbox[0]
    draw2.text((380 - w, y), line, fill="#059669", font=font)
    y += 50

img2.save("test_no_bidi_2.png")
print("2. Wrap inversé - sauvegardé")