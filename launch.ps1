# Lanza el dashboard HTML: arranca el servidor local y abre el navegador en
# modo kiosko a pantalla completa sobre el Hosyond (panel de 1024x600).
#
# Robustez: en vez de SOLO buscar un monitor que ya este a 1024x600 (que falla
# cuando Windows arranca el panel a 640x480), localizamos el panel por su
# resolucion maxima soportada (1024x600 -> es el Hosyond, no los 1920x1080),
# lo FORZAMOS a 1024x600, y posicionamos el kiosko en sus coordenadas reales.
$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
$port = 8787
$url  = "http://127.0.0.1:$port/"               # base: sondeo de readiness ($url + data.json)
$page = "http://127.0.0.1:$port/telemetry"      # página que se muestra en el kiosko (HUD sci-fi)

# Log con rotacion simple: los fallos de arranque quedan registrados, no ocultos.
$logFile = Join-Path $root 'launch.log'
function Log($m) { "$(Get-Date -Format s) $m" | Add-Content -Path $logFile -Encoding utf8 }
if ((Test-Path $logFile) -and (Get-Item $logFile).Length -gt 200KB) {
  Get-Content $logFile -Tail 200 | Set-Content $logFile -Encoding utf8
}
Log 'launch start'

# Python sin consola: el del PATH; si no, la instalacion por usuario mas reciente.
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $py) {
  $py = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*\pythonw.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $py) { Log 'ERROR: no se encontro pythonw.exe'; exit 1 }

# ¿ya responde el servidor? Si no, arrancarlo.
$ready = $false
try { Invoke-WebRequest -UseBasicParsing "$url`data.json" -TimeoutSec 1 | Out-Null; $ready = $true } catch {}
if (-not $ready) {
  Log "arrancando servidor con $py"
  Start-Process -FilePath $py -ArgumentList "server.py","--port",$port -WorkingDirectory $root -WindowStyle Hidden
  for ($i = 0; $i -lt 30; $i++) {
    try { Invoke-WebRequest -UseBasicParsing "$url`data.json" -TimeoutSec 1 | Out-Null; $ready = $true; break } catch { Start-Sleep -Milliseconds 500 }
  }
  if (-not $ready) { Log 'ERROR: el servidor no respondio en 15 s' }
}

# ---- Helper nativo: localizar el panel y fijarlo a 1024x600 -------------------
$disp = @"
using System;
using System.Runtime.InteropServices;
public static class DispCtl {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  static extern bool EnumDisplayDevices(string dev, uint i, ref DISPLAY_DEVICE d, uint flags);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  static extern int EnumDisplaySettings(string dev, int mode, ref DEVMODE dm);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  static extern int ChangeDisplaySettingsEx(string dev, ref DEVMODE dm, IntPtr h, uint flags, IntPtr p);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  struct DISPLAY_DEVICE {
    public int cb;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)]  public string DeviceName;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string DeviceString;
    public int StateFlags;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string DeviceID;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=128)] public string DeviceKey;
  }
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  struct DEVMODE {
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName;
    public ushort dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
    public uint dmFields;
    public int dmPositionX, dmPositionY; public uint dmDisplayOrientation, dmDisplayFixedOutput;
    public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName;
    public ushort dmLogPixels;
    public uint dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency;
    public uint dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;
  }
  const int CURRENT=-1; const uint DM_PELSWIDTH=0x80000, DM_PELSHEIGHT=0x100000; const uint CDS_DYNAMIC=0x00;  /* 0 = cambio temporal: no se guarda en el registro de Windows */ const int ACTIVE=0x1;

  static uint CurWidth(string dev){
    DEVMODE dm=new DEVMODE(); dm.dmSize=(ushort)Marshal.SizeOf(typeof(DEVMODE));
    if(EnumDisplaySettings(dev,CURRENT,ref dm)==0) return 0;
    return dm.dmPelsWidth;
  }
  // El panel Hosyond es el display activo con la resolucion ACTUAL mas pequena
  // (los monitores reales estan a 1920). Filtramos a <=1600 para no tocar jamas
  // un 1920x1080 aunque el panel este desconectado. No usamos el modo MAXIMO:
  // el driver Intel ahora expone modos escalados hasta 1920 tambien en el panel.
  public static string FindPanel(){
    string best=null; uint bestW=uint.MaxValue;
    DISPLAY_DEVICE d=new DISPLAY_DEVICE(); d.cb=Marshal.SizeOf(typeof(DISPLAY_DEVICE)); uint n=0;
    while(EnumDisplayDevices(null,n,ref d,0)){
      if((d.StateFlags & ACTIVE)!=0){
        uint cw=CurWidth(d.DeviceName);
        if(cw>0 && cw<=1600 && cw<bestW){ bestW=cw; best=d.DeviceName; }
      }
      n++; d=new DISPLAY_DEVICE(); d.cb=Marshal.SizeOf(typeof(DISPLAY_DEVICE));
    }
    return best;
  }
  // Fija dev a wxh (si hace falta) y devuelve "x,y" de su posicion actual. "" si no se puede.
  public static string EnsureMode(string dev,int w,int h){
    if(dev==null) return "";
    DEVMODE cur=new DEVMODE(); cur.dmSize=(ushort)Marshal.SizeOf(typeof(DEVMODE));
    EnumDisplaySettings(dev,CURRENT,ref cur);
    if(!(cur.dmPelsWidth==w && cur.dmPelsHeight==h)){
      DEVMODE t=new DEVMODE(); bool found=false; int i=0;
      while(true){ DEVMODE dm=new DEVMODE(); dm.dmSize=(ushort)Marshal.SizeOf(typeof(DEVMODE));
        if(EnumDisplaySettings(dev,i,ref dm)==0) break;
        if(dm.dmPelsWidth==w && dm.dmPelsHeight==h){ t=dm; found=true; break; } i++; }
      if(found){ t.dmFields=DM_PELSWIDTH|DM_PELSHEIGHT;
        ChangeDisplaySettingsEx(dev,ref t,IntPtr.Zero,CDS_DYNAMIC,IntPtr.Zero); }
    }
    DEVMODE pos=new DEVMODE(); pos.dmSize=(ushort)Marshal.SizeOf(typeof(DEVMODE));
    EnumDisplaySettings(dev,CURRENT,ref pos);
    return pos.dmPositionX + "," + pos.dmPositionY;
  }
}
"@
Add-Type -TypeDefinition $disp

$panelDev = [DispCtl]::FindPanel()
if (-not $panelDev) { Log 'AVISO: no se encontro el panel (<=1600 px); el kiosko ira a 0,0' } else { Log "panel: $panelDev" }
$pos      = [DispCtl]::EnsureMode($panelDev, 1024, 600)
if ($pos) { $x = ($pos -split ',')[0]; $y = ($pos -split ',')[1] } else { $x = 0; $y = 0 }

# Elegir navegador (Edge preferido, luego Chrome).
$edge   = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
# --force-device-scale-factor=1 evita que la escala DPI de Windows agrande el UI;
# --window-size fija el viewport a 1024x600 exactos.
$common = @("--window-position=$x,$y","--window-size=1024,600","--force-device-scale-factor=1",
            "--user-data-dir=$env:LOCALAPPDATA\claude-dash-kiosk",
            "--no-first-run","--no-default-browser-check","--disable-features=TranslateUI")

if (Test-Path $edge) {
  Start-Process -FilePath $edge -ArgumentList (@("--kiosk",$page,"--edge-kiosk-type=fullscreen") + $common)
} elseif (Test-Path $chrome) {
  Start-Process -FilePath $chrome -ArgumentList (@("--kiosk",$page) + $common)
} else { Log 'ERROR: ni Edge ni Chrome encontrados' }
Log 'launch done'
