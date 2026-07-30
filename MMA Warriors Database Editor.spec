# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['D:\\CodexFILES\\MMA Warriors\\database_editor.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('D:\\CodexFILES\\MMA Warriors\\assets\\database_editor_icon.ico', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'sounddevice', '_sounddevice_data'],
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
    name='MMA Warriors Database Editor',
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
    icon=['D:\\CodexFILES\\MMA Warriors\\assets\\database_editor_icon.ico'],
)
