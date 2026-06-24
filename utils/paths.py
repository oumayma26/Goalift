# utils/paths.py
import os
import sys
from pathlib import Path

def get_app_data_dir() -> str:
    """Dossier de données persistant de l'application."""
    if getattr(sys, 'frozen', False):
        # PyInstaller : AppData/Local/Goalift
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'Goalift'
    else:
        # Développement : dossier data/ à côté du projet
        base = Path(__file__).resolve().parent.parent / 'data'
    
    base.mkdir(parents=True, exist_ok=True)
    return str(base)

def get_db_path() -> str:
    return get_app_data_dir()

def get_uploads_dir(subfolder: str = "") -> str:
    uploads = Path(get_app_data_dir()) / 'uploads'
    if subfolder:
        uploads = uploads / subfolder
    uploads.mkdir(parents=True, exist_ok=True)
    return str(uploads)