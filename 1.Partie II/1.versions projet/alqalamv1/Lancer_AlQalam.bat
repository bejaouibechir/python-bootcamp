@echo off
chcp 65001 >nul
title Al Qalam — Gestion de Stock

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║    📚  Al Qalam — Gestion de Stock       ║
echo  ║            Version 1.0.0                 ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Aller dans le dossier du script (même si lancé depuis ailleurs)
cd /d "%~dp0"

:: Vérifier que Python est disponible
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python introuvable.
    echo  Installez Python 3.11+ depuis https://www.python.org
    pause
    exit /b 1
)

:: Vérifier que customtkinter est installé, sinon l'installer
py -3 -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Installation de customtkinter...
    py -3 -m pip install customtkinter --quiet
)

:: Lancer l'application
echo  Démarrage de l'application...
echo.
py -3 main.py

:: Si l'application plante, afficher l'erreur
if errorlevel 1 (
    echo.
    echo  [ERREUR] L'application s'est arrêtée de façon inattendue.
    pause
)
