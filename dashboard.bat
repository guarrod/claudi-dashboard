@echo off
REM ============================================================================
REM  dashboard.bat - Levanta el dashboard directamente:
REM    1) arranca el servidor local (oculto) si no esta ya respondiendo
REM    2) abre el HUD a pantalla completa en la PANTALLA 3 (panel 1024x600)
REM  Doble clic para lanzarlo. Para salir del kiosko: Alt+F4.
REM ============================================================================
cd /d "%~dp0"

set "PORT=8787"
set "URL=http://127.0.0.1:%PORT%/telemetry"

REM --- python (oculto, sin consola). Usa tu Python310; si no, el del PATH ---
set "PY=%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"
if not exist "%PY%" set "PY=pythonw"

REM --- 1) servidor: si /data.json no responde, arrancarlo y esperar ---
curl -s -o nul --max-time 1 "http://127.0.0.1:%PORT%/data.json"
if errorlevel 1 (
  echo Arrancando servidor...
  start "" "%PY%" server.py --port %PORT%
  for /l %%i in (1,1,20) do (
    curl -s -o nul --max-time 1 "http://127.0.0.1:%PORT%/data.json" && goto :ready
    timeout /t 1 /nobreak >nul
  )
)
:ready

REM --- 2) abrir el kiosko en la pantalla 3 (coordenadas -2944,0) ---
REM  La ventana se abre en el monitor que contiene esa coordenada = DISPLAY3.
start "" msedge --kiosk "%URL%" --edge-kiosk-type=fullscreen ^
  --window-position=-2944,0 --window-size=1024,600 --force-device-scale-factor=1 ^
  --user-data-dir="%LOCALAPPDATA%\claude-dash-kiosk" --no-first-run --no-default-browser-check
