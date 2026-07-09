from pathlib import Path

from PyInstaller.building.build_main import Analysis, EXE, PYZ


project_root = Path.cwd()
resource_files = [
    (str(path), "resources")
    for path in (project_root / "resources").glob("*.json")
]

a = Analysis(
    ["run.py"],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=resource_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AutomacaoPJE",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
