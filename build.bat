@echo off
chcp 65001 >nul
cls
echo ============================================
echo    Goalift - Build et Deploy
echo ============================================
echo.

set "PROJECT_DIR=C:\Users\Oumayma\OneDrive\Bureau\Dev\Goalift"
cd /d "%PROJECT_DIR%"

:: -- Verifier venv --
if not exist "venv\Scripts\python.exe" (
    echo [1/6] Creation du venv...
    python -m venv venv
) else (
    echo [1/6] Venv existant trouve
)

:: -- Activer venv --
echo [2/6] Activation du venv...
call venv\Scripts\activate.bat

:: -- Installer dependances --
echo [3/6] Installation des dependances...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1
python -m pip install pyinstaller >nul 2>&1
echo      OK

:: -- Nettoyer anciens builds --
echo [4/6] Nettoyage des anciens builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec
echo      OK

:: -- Build avec PyInstaller --
echo [5/6] Build PyInstaller...
python -m PyInstaller --name=Goalift --windowed --onefile --add-data "assets;assets" --hidden-import=customtkinter --hidden-import=PIL --clean main.py

if errorlevel 1 (
    echo      ERREUR lors du build
    pause
    exit /b 1
)
echo      Build termine

:: -- Verifier resultat --
echo [6/6] Verification...
if exist "dist\Goalift.exe" (
    echo      dist\Goalift.exe cree
    echo.
    echo ============================================
    echo    BUILD REUSSI
echo ============================================
    echo.
    echo Fichier : %PROJECT_DIR%\dist\Goalift.exe
    echo Taille  :
    dir "dist\Goalift.exe" | findstr "Goalift.exe"
) else (
    echo      Fichier non trouve
)

echo.
pause