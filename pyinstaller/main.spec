# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

spec_dir = Path(SPECPATH).resolve()
project_root = spec_dir.parent
renderer_dir = project_root / "renderer"
main_script = project_root / "src" / "main.py"
target_arch = os.environ.get("PYINSTALLER_TARGET_ARCH") or None

a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(renderer_dir), 'renderer')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ZPLConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ZPLConverter',
)
