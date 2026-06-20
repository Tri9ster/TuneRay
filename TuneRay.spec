# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sonos_eq_gui_advanced.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'soco', 'pynput', 'strings', 'controller', 'models'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_qt_mac.py'],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# macOS 15 で qdarwinpermissionplugin_location の静的イニシャライザが
# CFBundleGetMainBundle()=NULL を呼びクラッシュするため除外する
a.binaries = [b for b in a.binaries if 'qdarwinpermissionplugin' not in b[0].lower()]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TuneRay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/TuneRay.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TuneRay',
)

app = BUNDLE(
    coll,
    name='TuneRay.app',
    icon='src/TuneRay.icns',
    bundle_identifier='com.tuneray.sonos-eq',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'CFBundleName': 'TuneRay',
        'CFBundleDisplayName': 'TuneRay',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.tuneray.sonos-eq',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'MIT License',
    },
)
