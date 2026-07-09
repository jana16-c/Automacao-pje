param()

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$projectRoot = Split-Path -Parent $PSScriptRoot
$releaseRoot = Join-Path $projectRoot "entrega\AutomacaoPJE_Python"

if (Test-Path $releaseRoot) {
    Remove-Item -Recurse -Force $releaseRoot
}

New-Item -ItemType Directory -Path $releaseRoot | Out-Null
New-Item -ItemType Directory -Path (Join-Path $releaseRoot "src") | Out-Null

Copy-Item -Recurse -Force (Join-Path $projectRoot "src\pje_automation") (Join-Path $releaseRoot "src\pje_automation")
Copy-Item -Recurse -Force (Join-Path $projectRoot "resources") (Join-Path $releaseRoot "resources")
Get-ChildItem -Path $releaseRoot -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

@'
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from pje_automation.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -Encoding UTF8 (Join-Path $releaseRoot "AutomacaoPJE.py")

@'
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from pje_automation.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -Encoding UTF8 (Join-Path $releaseRoot "AutomacaoPJE.pyw")

@'
openpyxl>=3.1,<4
selenium>=4.24,<5
requests>=2.32,<3
'@ | Set-Content -Encoding UTF8 (Join-Path $releaseRoot "requirements.txt")

@'
@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 -m venv .venv || exit /b 1
    ) else (
        python -m venv .venv || exit /b 1
    )
    call ".venv\Scripts\python.exe" -m pip install --upgrade pip || exit /b 1
    call ".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "AutomacaoPJE.pyw"
'@ | Set-Content -Encoding ASCII (Join-Path $releaseRoot "Iniciar_AutomacaoPJE.bat")

@'
# Automacao PJe em Python

1. Execute `Iniciar_AutomacaoPJE.bat`.
2. Na primeira vez, ele cria `.venv` e instala as dependencias.
3. Depois disso, a interface abre pelo `pythonw`, sem usar `.exe`.

Execucao manual:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\pythonw.exe .\AutomacaoPJE.pyw
```
'@ | Set-Content -Encoding UTF8 (Join-Path $releaseRoot "README.md")
