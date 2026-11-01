@echo off
REM dashboard.bat - doble clic para lanzar el dashboard (servidor + kiosko).
REM Delega en launch.ps1, que detecta Python y el panel de 1024x600 solo.
REM Para salir del kiosko: Alt+F4.
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0launch.ps1"
