# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve()

# Authoritative game-package definition. Build Portable.bat invokes this file
# directly. Keep optional dependency decisions here and cover them with the
# static shipping regression before changing the packaged runtime graph.

a = Analysis(
    [str(PROJECT_ROOT / 'main.py')],
    pathex=[],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'assets'), 'assets'),
        (str(PROJECT_ROOT / 'country_flags'), 'country_flags'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Preserve the canonical batch build's established dependency discovery.
    # Development-only numpy tools are outside main.py's import graph, and the
    # game does not import sounddevice; neither is force-excluded here.
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MMA Warriors',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(PROJECT_ROOT / 'assets' / 'app_icon.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MMA Warriors',
)
