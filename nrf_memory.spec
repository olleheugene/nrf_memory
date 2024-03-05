# -*- mode: python ; coding: utf-8 -*-

def get_resources():
    data_files = []
    for file_name in os.listdir('resources'):
        data_files.append((os.path.join('resources', file_name), '.'))
    return data_files

block_cipher = None


a = Analysis(
    ['nrf_memory.py'],
    pathex=[],
    binaries=[],
    datas=get_resources(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts + [('O','','OPTION')],
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=False,
    name='nrf_memory',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    upx_exclude=[],
    icon='resources/application.ico',
    runtime_tmpdir=None,
    console=True,
)
