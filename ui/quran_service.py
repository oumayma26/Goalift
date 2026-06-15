"""
services/quran_service.py
Service pour récupérer des ayats du Coran en arabe uniquement.
API : https://alquran.cloud/api (GRATUIT, sans clé)
"""

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
import hashlib


@dataclass
class QuranAyat:
    """Représente un ayat en arabe."""
    surah_number: int
    surah_name_arabic: str
    surah_name_french: str
    ayat_number: int
    arabic_text: str


class QuranService:
    """
    Service gratuit pour récupérer des ayats du Coran.
    API : https://alquran.cloud/api
    """

    BASE_URL = "https://api.alquran.cloud/v1"
    CACHE_DIR = Path("assets/quran_cache")

    # Ayats vérifiés et pertinents pour la motivation/prière
    # Format : (sourate, ayat, description)
    VERIFIED_AYATS = [
        # Sourate 94 : Al-Inshirah (Le Développement)
        (94, 5, "Avec la difficulté vient la facilité"),
        (94, 6, "Avec la difficulté vient la facilité - répété pour certitude"),

        # Sourate 2 : Al-Baqarah (La Vache)
        (2, 286, "Allah n'impose à aucune âme une charge supérieure à sa capacité"),

        # Sourate 39 : Az-Zumar (Les Groupes)
        (39, 53, "Ne désespérez pas de la miséricorde d'Allah"),

        # Sourate 2 : Al-Baqarah
        (2, 153, "Ô les croyants ! Cherchez secours dans la patience et la prière"),

        # Sourate 3 : Al-Imran (La Famille d'Imran)
        (3, 200, "Ô les croyants ! Endurez et surpassez en endurance"),

        # Sourate 70 : Al-Ma'arij (Les Voies d'Ascension)
        (70, 5, "Sois donc patient, d'une patience magnifique"),

        # Sourate 14 : Ibrahim
        (14, 7, "Si vous remerciez, Je vous accroîtrai"),

        # Sourate 29 : Al-Ankabut (L'Araignée)
        (29, 69, "Ceux qui luttent pour Notre cause, Nous les guiderons certes sur Nos voies"),

        # Sourate 13 : Ar-Ra'd (Le Tonnerre)
        (13, 11, "Allah ne change pas l'état d'un peuple jusqu'à ce qu'ils ne changent ce qui est en eux-mêmes"),

        # Sourate 2 : Al-Baqarah
        (2, 269, "Il donne la sagesse à qui Il veut"),

        # Sourate 65 : At-Talaq (Le Divorce)
        (65, 3, "Quiconque met sa confiance en Allah, Il lui suffit"),

        # Sourate 3 : Al-Imran
        (3, 159, "C'est Allah qui est votre Protecteur"),

        # Sourate 2 : Al-Baqarah
        (2, 216, "Le bien peut être dans ce que vous aimez pas"),

        # Sourate 9 : At-Tawbah (Le Repentir)
        (9, 51, "Dis : Rien ne nous atteindra en dehors de ce qu'Allah a prescrit pour nous"),

        # Sourate 57 : Al-Hadid (Le Fer)
        (57, 22, "Aucun malheur n'atteint la terre ni vos personnes sans qu'il ne soit dans un Livre avant que Nous ne le créions"),

        # Sourate 2 : Al-Baqarah
        (2, 45, "Cherchez secours dans la patience et la prière"),

        # Sourate 2 : Al-Baqarah
        (2, 155, "Nous vous éprouverons par quelque peur, la faim, la perte de biens..."),

        # Sourate 3 : Al-Imran
        (3, 139, "Ne vous découragez pas et ne vous affligez pas"),

        # Sourate 64 : At-Taghabun (La Grande Déception)
        (64, 11, "Nul malheur n'atteint quelqu'un sans la permission d'Allah"),

        # Sourate 2 : Al-Baqarah
        (2, 286, "Notre Seigneur ! Ne nous charge pas d'un fardeau que nous n'avons pas la force de supporter"),
    ]

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get_ayat(self, surah: int, ayat: int) -> Optional[QuranAyat]:
        """
        Récupère un ayat spécifique en arabe uniquement.
        """
        cache_key = hashlib.md5(f"{surah}_{ayat}_arabic".encode()).hexdigest()
        cache_file = self.CACHE_DIR / f"{cache_key}.json"

        # Vérifier cache
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self._parse_ayat(data)

        # Appel API - édition arabe uniquement
        url = f"{self.BASE_URL}/ayah/{surah}:{ayat}/editions/quran-uthmani"

        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data.get("code") == 200:
                # Sauvegarder en cache
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)

                return self._parse_ayat(data)

        except Exception as e:
            print(f"⚠️ Erreur API Quran: {e}")

        return None

    def _parse_ayat(self, data: dict) -> Optional[QuranAyat]:
        """Parse la réponse API."""
        try:
            ayat_data = data["data"][0]

            return QuranAyat(
                surah_number=ayat_data["surah"]["number"],
                surah_name_arabic=ayat_data["surah"]["name"],
                surah_name_french=ayat_data["surah"]["englishName"],
                ayat_number=ayat_data["numberInSurah"],
                arabic_text=ayat_data["text"]
            )
        except (KeyError, IndexError) as e:
            print(f"⚠️ Erreur parsing: {e}")
            return None

    def get_random_ayat(self) -> Optional[QuranAyat]:
        """Récupère un ayat vérifié aléatoire."""
        import random
        surah, ayat, _ = random.choice(self.VERIFIED_AYATS)
        return self.get_ayat(surah, ayat)

    def get_ayat_by_theme(self, theme: str) -> Optional[QuranAyat]:
        """
        Récupère un ayat par thème.
        Thèmes : patience, gratitude, confiance, effort, sagesse
        """
        import random

        themes = {
            "patience": [(2, 153), (3, 200), (70, 5), (2, 45)],
            "gratitude": [(14, 7)],
            "confiance": [(39, 53), (65, 3), (3, 159), (9, 51)],
            "effort": [(94, 5), (94, 6), (29, 69), (2, 286)],
            "sagesse": [(2, 269), (13, 11), (57, 22)],
            "nouveau_depart": [(2, 216), (3, 139), (64, 11)],
        }

        refs = themes.get(theme, [(94, 5)])  # Fallback par défaut
        surah, ayat = random.choice(refs)

        return self.get_ayat(surah, ayat)

    def get_all_themes(self) -> List[str]:
        """Retourne la liste des thèmes disponibles."""
        return ["patience", "gratitude", "confiance", "effort", "sagesse", "nouveau_depart"]