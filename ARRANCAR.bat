@echo off
REM Doble clic aqui para arrancar la competencia en este computador.
REM No usa el .exe empaquetado, asi que ningun antivirus se mete.
cd /d "%~dp0"
title GeoGuessr Competencia - NO CERRAR
python servidor.py %*
echo.
echo El servidor se detuvo. Puedes cerrar esta ventana.
pause
