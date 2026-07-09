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
