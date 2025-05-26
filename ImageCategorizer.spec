
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/static', 'app/static'),
        ('app/templates', 'app/templates'),
        ('openai_client.py', '.'),
        ('config', 'config'),  # Include config directory with categories.json
    ],
    hiddenimports=[
        'flask',
        'openai',
        'pandas',
        'PIL',
        'PIL.Image',
        'requests',
        'httpx',
        'webbrowser',
        'keyring',
        'app.web_categorizer',
        'app.image_categorizer',
        'app.openai_fixed',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Image Categorizer',
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
    icon='ImageCategorizer.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Image Categorizer',
)

app = BUNDLE(
    coll,
    name='Image Categorizer.app',
    icon='ImageCategorizer.icns',
    bundle_identifier='com.styledstock.imagecategorizer',
    info_plist={
        'CFBundleName': 'Image Categorizer',
        'CFBundleDisplayName': 'Image Categorizer',
        'CFBundleExecutable': 'Image Categorizer',
        'CFBundleIdentifier': 'com.styledstock.imagecategorizer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 Styled Stock',
        'NSHighResolutionCapable': True,
        'LSEnvironment': {
            'MACOS_APP_BUNDLE': '1',
        },
        'NSAppleEventsUsageDescription': 'This app needs to access the browser to display the web interface.',
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True,
        },
    },
)
