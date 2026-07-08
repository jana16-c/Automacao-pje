param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    throw "Ambiente virtual não encontrado em .venv."
}

if ($Clean) {
    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
    }
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
    }
}

& ".venv\\Scripts\\python.exe" -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar dependências de build."
}

& ".venv\\Scripts\\python.exe" -m PyInstaller --noconfirm --clean "AutomacaoPJE.spec"
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar o executável."
}

Write-Host ""
Write-Host "Build concluído."
Write-Host "EXE: $projectRoot\\dist\\AutomacaoPJE.exe"
