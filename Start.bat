@echo off
TITLE Simulatore Patente Nautica
:: %~dp0 è il comando magico che dice: "La cartella è QUESTA, ovunque essa sia"
cd /d "%~dp0"

echo ------------------------------------------------
echo  AVVIO SIMULATORE IN CORSO...
echo ------------------------------------------------
echo.

:: Lancia l'app usando il comando python
python -m streamlit run app.py

:: Se c'è un errore, non chiudere subito la finestra
if %errorlevel% neq 0 pause