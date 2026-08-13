@echo off
REM Arranca el servidor de datos y abre el dashboard HTML en kiosko sobre el
REM Hosyond (1024x600). Doble clic para lanzarlo, o se ejecuta solo al iniciar
REM sesion via el acceso directo de la carpeta de Inicio.
powershell -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File "%~dp0launch.ps1"
