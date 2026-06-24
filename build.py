#!/usr/bin/env python3
"""
Goalift - Script de build professionnel (style Family Manager)
===============================================================
Génère : .exe autonome + installateur NSIS + update.json
Tout est automatisé, aucune commande manuelle requise.

Usage :
    python build_goalift.py          # Build complet
    python build_goalift.py clean     # Nettoyer
"""

import os
import sys
import shutil
import subprocess
import importlib.util
import urllib.request
import zipfile
import json
import hashlib
from pathlib import Path
from datetime import datetime


# ==================== CONFIGURATION ====================

APP_NAME = "Goalift"
APP_VERSION = "1.0.0"  # ← Bump ici pour les mises à jour
APP_PUBLISHER = "Goalift Team"
MAIN_SCRIPT = "main.py"
ICON_PATH = "assets/icon.ico"

# URL de base où seront hébergés les fichiers (optionnel)
UPDATE_BASE_URL = "https://ton-site.com/downloads"

NSIS_URL = "https://sourceforge.net/projects/nsis/files/NSIS%203/3.10/nsis-3.10.zip/download"
NSIS_LOCAL_ZIP = "nsis.zip"
NSIS_EXTRACT_DIR = "nsis_portable"


# ==================== UTILITAIRES ====================

def print_step(step_num, total, title):
    print(f"\n{":"*60}")
    print(f"  Étape {step_num}/{total} : {title}")
    print(f"{":"*60}")


def run_command(cmd, description, cwd=None, timeout=300):
    print(f"\n   ▶ {description}")
    cmd_str = " ".join(str(c) for c in cmd)
    print(f"     {cmd_str[:100]}{"..." if len(cmd_str) > 100 else ""}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout après {timeout}s")
        return False, "Timeout"
    except Exception as e:
        print(f"   ❌ Exception : {e}")
        return False, str(e)
    if result.returncode != 0:
        print(f"   ❌ ERREUR (code {result.returncode})")
        if result.stderr and len(result.stderr) < 800:
            print(f"   {result.stderr[:500]}")
        return False, result.stderr
    print(f"   ✅ OK")
    return True, result.stdout


def ensure_module(module_name, pip_name=None):
    if pip_name is None:
        pip_name = module_name
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        return True
    print(f"   📦 Installation de {pip_name}...")
    success, _ = run_command([sys.executable, "-m", "pip", "install", pip_name, "--quiet"], f"pip install {pip_name}")
    return success


def find_nsis():
    paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        str(Path(NSIS_EXTRACT_DIR) / "nsis-3.10" / "makensis.exe"),
        str(Path(NSIS_EXTRACT_DIR) / "makensis.exe"),
    ]
    for p in paths:
        if Path(p).exists():
            return str(p)
    found = shutil.which("makensis")
    if found:
        return found
    return None


def download_nsis_portable():
    print(f"\n   📥 Téléchargement de NSIS portable...")
    nsis_dir = Path(NSIS_EXTRACT_DIR)
    if nsis_dir.exists():
        exe_path = nsis_dir / "nsis-3.10" / "makensis.exe"
        if exe_path.exists():
            print(f"   ✅ NSIS portable déjà présent")
            return str(exe_path)
        exe_path = nsis_dir / "makensis.exe"
        if exe_path.exists():
            return str(exe_path)
    try:
        print(f"   ⬇️  Téléchargement depuis SourceForge...")
        urllib.request.urlretrieve(NSIS_URL, NSIS_LOCAL_ZIP)
        print(f"   ✅ Téléchargé : {NSIS_LOCAL_ZIP}")
        print(f"   📂 Extraction...")
        with zipfile.ZipFile(NSIS_LOCAL_ZIP, "r") as z:
            z.extractall(NSIS_EXTRACT_DIR)
        Path(NSIS_LOCAL_ZIP).unlink(missing_ok=True)
        exe_path = nsis_dir / "nsis-3.10" / "makensis.exe"
        if exe_path.exists():
            print(f"   ✅ NSIS prêt : {exe_path}")
            return str(exe_path)
        return None
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return None


def install_nsis():
    print(f"\n   🔧 NSIS non trouvé — tentative d'installation...")
    print(f"   📌 Méthode 1 : winget...")
    success, _ = run_command(["winget", "install", "NSIS.NSIS", "--silent", "--accept-package-agreements"], "winget install NSIS", timeout=60)
    if success:
        nsis = find_nsis()
        if nsis:
            return nsis
    print(f"   📌 Méthode 2 : Chocolatey...")
    success, _ = run_command(["powershell", "-Command", "choco install nsis -y"], "choco install NSIS", timeout=60)
    if success:
        nsis = find_nsis()
        if nsis:
            return nsis
    print(f"   📌 Méthode 3 : Téléchargement portable...")
    nsis = download_nsis_portable()
    if nsis:
        return nsis
    return None


# ==================== GÉNÉRATION UPDATE.JSON ====================

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_update_json(exe_path: Path, release_notes: str = "", mandatory: bool = False) -> Path:
    print(f"\n   📝 Génération de update.json...")
    if not exe_path.exists():
        print(f"   ❌ Exécutable non trouvé : {exe_path}")
        return None
    checksum = compute_sha256(exe_path)
    size = exe_path.stat().st_size
    update_data = {
        "version": APP_VERSION,
        "url": f"{UPDATE_BASE_URL}/{exe_path.name}",
        "checksum": checksum,
        "size_bytes": size,
        "release_notes": release_notes,
        "min_version": "1.0.0",
        "mandatory": mandatory,
        "published_at": datetime.now().isoformat()
    }
    output = Path("update.json")
    output.write_text(json.dumps(update_data, indent=2), encoding="utf-8")
    print(f"   ✅ {output.name} généré")
    print(f"   📦 Version : {APP_VERSION}")
    print(f"   🔐 SHA-256 : {checksum[:16]}...")
    print(f"   📊 Taille : {size / 1024 / 1024:.1f} Mo")
    return output


# ==================== ÉTAPES DE BUILD ====================

def clean_build():
    dirs = ["build", "dist", f"{APP_NAME}.spec", "installer"]
    for d in dirs:
        path = Path(d)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"   🗑️  {d}")


def prepare_assets():
    Path("assets").mkdir(exist_ok=True)
    has_icon = Path(ICON_PATH).exists()
    if not has_icon:
        print(f"   ℹ️  Pas d'icône personnalisée (optionnel)")
    return has_icon


def build_executable():
    if not ensure_module("PyInstaller", "pyinstaller"):
        print("❌ PyInstaller indisponible")
        sys.exit(1)
    cmd = [sys.executable, "-m", "PyInstaller", "--name", APP_NAME, "--onefile", "--windowed", "--clean", "--noconfirm"]
    if Path(ICON_PATH).exists():
        cmd.extend(["--icon", ICON_PATH])
    cmd.extend([
        "--add-data", f"assets{os.pathsep}assets",
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._imagingtk",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "sqlite3",
        "--hidden-import", "tkinter",
        "--hidden-import", "_tkinter",
    ])
    cmd.append(MAIN_SCRIPT)
    success, _ = run_command(cmd, "Compilation PyInstaller", timeout=300)
    if not success:
        print("\n❌ Build échoué !")
        sys.exit(1)


def create_installer_script(has_icon):
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)
    exe_source = Path("dist") / f"{APP_NAME}.exe"
    exe_dest = installer_dir / f"{APP_NAME}.exe"
    if not exe_source.exists():
        print(f"❌ Exécutable non trouvé : {exe_source}")
        sys.exit(1)
    shutil.copy2(exe_source, exe_dest)

    # --- Génération du texte NSIS en Python pur, pas dans une f-string ---
    if has_icon:
        icon_define = (
            "\n!define MUI_ICON \"icon.ico\"\n"
            "!define MUI_UNICON \"icon.ico\"\n"
        )
        icon_shortcuts = (
            "    CreateShortcut \"$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk\" "
            "\"$INSTDIR\\${APP_EXE}\" \"\" \"$INSTDIR\\icon.ico\" 0\n"
            "    CreateShortcut \"$DESKTOP\\${APP_NAME}.lnk\" "
            "\"$INSTDIR\\${APP_EXE}\" \"\" \"$INSTDIR\\icon.ico\" 0\n"
        )
        shutil.copy2(ICON_PATH, installer_dir / "icon.ico")
    else:
        icon_define = ""
        icon_shortcuts = (
            "    CreateShortcut \"$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk\" "
            "\"$INSTDIR\\${APP_EXE}\"\n"
            "    CreateShortcut \"$DESKTOP\\${APP_NAME}.lnk\" "
            "\"$INSTDIR\\${APP_EXE}\"\n"
        )

    nsi = installer_dir / "installer.nsi"
    nsi.write_text(
        "; Goalift Installer\n"
        f"!define APP_NAME \"{APP_NAME}\"\n"
        f"!define APP_VERSION \"{APP_VERSION}\"\n"
        f"!define APP_PUBLISHER \"{APP_PUBLISHER}\"\n"
        f"!define APP_EXE \"{APP_NAME}.exe\"\n"
        "\n"
        "SetCompressor lzma\n"
        "!include \"MUI2.nsh\"\n"
        "!include \"LogicLib.nsh\"\n"
        "\n"
        "Name \"${APP_NAME} ${APP_VERSION}\"\n"
        f"OutFile \"../{APP_NAME}_Setup_{APP_VERSION}.exe\"\n"
        "InstallDir \"$PROGRAMFILES64\\${APP_NAME}\"\n"
        "RequestExecutionLevel admin\n"
        f"{icon_define}"
        "\n"
        "!insertmacro MUI_PAGE_WELCOME\n"
        "!insertmacro MUI_PAGE_LICENSE \"license.txt\"\n"
        "!insertmacro MUI_PAGE_DIRECTORY\n"
        "!insertmacro MUI_PAGE_INSTFILES\n"
        "!insertmacro MUI_PAGE_FINISH\n"
        "\n"
        "!insertmacro MUI_UNPAGE_WELCOME\n"
        "!insertmacro MUI_UNPAGE_CONFIRM\n"
        "!insertmacro MUI_UNPAGE_INSTFILES\n"
        "!insertmacro MUI_UNPAGE_FINISH\n"
        "\n"
        "!insertmacro MUI_LANGUAGE \"French\"\n"
        "\n"
        "Section \"Install\"\n"
        "    SetOutPath \"$INSTDIR\"\n"
        "    File \"${APP_EXE}\"\n"
        "    File \"icon.ico\"\n"
        "    CreateDirectory \"$INSTDIR\\assets\"\n"
        "    CreateDirectory \"$INSTDIR\\data\"\n"
        "    CreateDirectory \"$SMPROGRAMS\\${APP_NAME}\"\n"
        f"{icon_shortcuts}"
        "    CreateShortcut \"$SMPROGRAMS\\${APP_NAME}\\Désinstaller.lnk\" \"$INSTDIR\\uninstall.exe\"\n"
        "    WriteRegStr HKLM \"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}\" \"DisplayName\" \"${APP_NAME}\"\n"
        "    WriteRegStr HKLM \"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}\" \"UninstallString\" \"$INSTDIR\\uninstall.exe\"\n"
        "    WriteRegStr HKLM \"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}\" \"DisplayVersion\" \"${APP_VERSION}\"\n"
        "    WriteRegStr HKLM \"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}\" \"Publisher\" \"${APP_PUBLISHER}\"\n"
        "    WriteRegStr HKLM \"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}\" \"DisplayIcon\" \"$INSTDIR\\icon.ico\"\n"
        "    WriteUninstaller \"$INSTDIR\\uninstall.exe\"\n"
        "SectionEnd\n"
        "\n"
        "Section \"Uninstall\"\n"
        "    Delete \"$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk\"\n"
        "    Delete \"$SMPROGRAMS\\${APP_NAME}\\Désinstaller.lnk\"\n"
        "    RMDir \"$SMPROGRAMS\\${APP_NAME}\"\n"
        "    Delete \"$DESKTOP\\${APP_NAME}.lnk\"\n"
        "    Delete \"$INSTDIR\\${APP_EXE}\"\n"
        "    Delete \"$INSTDIR\\uninstall.exe\"\n"
        "    Delete \"$INSTDIR\\icon.ico\"\n"
        "    MessageBox MB_YESNO \"Supprimer les données utilisateur ?\" /SD IDNO IDYES delete_data IDNO skip_delete\n"
        "    delete_data:\n"
        "        RMDir /r \"$INSTDIR\\data\"\n"
        "        Goto continue_delete\n"
        "    skip_delete:\n"
        f"        CreateDirectory \"$DESKTOP\\{APP_NAME}_Sauvegarde\"\n"
        f"        CopyFiles \"$INSTDIR\\data\\*.*\" \"$DESKTOP\\{APP_NAME}_Sauvegarde\\\"\n"
        "        MessageBox MB_OK \"Données sauvegardées sur le Bureau\"\n"
        "    continue_delete:\n"
        "    RMDir \"$INSTDIR\"\n"
        "    DeleteRegKey HKLM \"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}\"\n"
        "SectionEnd\n",
        encoding="utf-8"
    )

    license_file = installer_dir / "license.txt"
    license_file.write_text(
        f"Goalift v{APP_VERSION}\n\n"
        f"Copyright (c) 2024 {APP_PUBLISHER}\n"
        "Usage personnel gratuit.\n",
        encoding="utf-8"
    )
    return nsi


def build_installer(has_icon):
    nsis_path = find_nsis()
    if not nsis_path:
        print(f"\n   🔧 NSIS non trouvé — tentative d'installation...")
        nsis_path = install_nsis()
    if not nsis_path:
        print(f"\n   ❌ NSIS indisponible. Installateur non généré.")
        print(f"   💡 Installez NSIS manuellement : https://nsis.sourceforge.io/Download")
        return False
    print(f"\n   ✅ NSIS : {nsis_path}")
    nsi_script = create_installer_script(has_icon)
    success, output = run_command([nsis_path, str(nsi_script)], "Compilation NSIS")
    if not success:
        print(f"\n   ❌ Détail de l'erreur NSIS :")
        print(f"   {output[-500:] if len(output) > 500 else output}")
        return False
    installer = Path(f"{APP_NAME}_Setup_{APP_VERSION}.exe")
    if installer.exists():
        size_mb = installer.stat().st_size / (1024 * 1024)
        print(f"   ✅ Installateur : {installer.name} ({size_mb:.1f} Mo)")
        return True
    return False


def show_summary():
    print(f"\n{":"*60}")
    print("  ✅ BUILD TERMINÉ !")
    print(f"{":"*60}")
    portable = Path("dist") / f"{APP_NAME}.exe"
    installer = Path(f"{APP_NAME}_Setup_{APP_VERSION}.exe")
    update_json = Path("update.json")
    print("\n📁 Fichiers générés :\n")
    if portable.exists():
        size = portable.stat().st_size / (1024 * 1024)
        print(f"   📌 PORTABLE")
        print(f"      {portable}")
        print(f"      {size:.1f} Mo")
    if installer.exists():
        size = installer.stat().st_size / (1024 * 1024)
        print(f"\n   📌 INSTALLATEUR (recommandé)")
        print(f"      {installer}")
        print(f"      {size:.1f} Mo")
    if update_json.exists():
        print(f"\n   📌 MISE À JOUR")
        print(f"      {update_json}")
        print(f"      À uploader sur : {UPDATE_BASE_URL}/")
    print(f"\n🚀 Pour distribuer :")
    if installer.exists():
        print(f"   → Uploadez '{installer.name}' et 'update.json' sur {UPDATE_BASE_URL}/")
    else:
        print(f"   → Zippez le dossier 'dist/' et distribuez")


# ==================== MAIN ====================

def main():
    print(f"{":"*60}")
    print(f"  Build {APP_NAME} v{APP_VERSION}")
    print(f"  Python : {sys.executable}")
    print(f"{":"*60}")
    if not Path(MAIN_SCRIPT).exists():
        print(f"\n❌ {MAIN_SCRIPT} introuvable !")
        sys.exit(1)
    print_step(1, 5, "Nettoyage")
    clean_build()
    print_step(2, 5, "Préparation des assets")
    has_icon = prepare_assets()
    print_step(3, 5, "Build de l'exécutable")
    build_executable()
    print_step(4, 5, "Création de l'installateur")
    build_installer(has_icon)
    print_step(5, 5, "Génération update.json")
    exe_path = Path("dist") / f"{APP_NAME}.exe"
    generate_update_json(
        exe_path=exe_path,
        release_notes=(
            "🚀 Nouveau : Goalift v1.0.0\n"
            "- Gestion de buts et vision board\n"
            "- Interface moderne avec customtkinter"
        ),
        mandatory=False
    )
    show_summary()


if __name__ == "__main__":
    main()