import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import arabic_reshaper
from bidi.algorithm import get_display

text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

# Reshape + Bidi
reshaped = arabic_reshaper.reshape(text)
display = get_display(reshaped)

# Charger la police arabe
prop = fm.FontProperties(fname='assets/fonts/ScheherazadeNew-Medium.ttf', size=32)

fig, ax = plt.subplots(figsize=(10, 2), facecolor='#F0FDF4')
ax.text(0.5, 0.5, display, fontproperties=prop, 
        ha='center', va='center', color='#059669')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

plt.savefig('test_arabic_mpl.png', dpi=150, bbox_inches='tight', 
            facecolor='#F0FDF4', pad_inches=0.2)
print("Image sauvegardée: test_arabic_mpl.png")