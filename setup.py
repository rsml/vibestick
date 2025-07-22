"""
py2app setup script for Vibestick

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['vibestick.py']
DATA_FILES = [
    ('', ['assets']),
    ('', ['config']),
    ('', ['images']),
    ('', ['src']),
    ('', ['main.py']),
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'assets/vibestick-icon.icns',  # We'll need to convert PNG to ICNS
    'plist': {
        'CFBundleName': 'Vibestick',
        'CFBundleDisplayName': 'Vibestick',
        'CFBundleGetInfoString': "StreamDeck Dual Control",
        'CFBundleIdentifier': "com.rossthedev.vibestick",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': u"Copyright © 2025, Ross Warren, MIT License",
        'LSUIElement': False,  # Show in dock
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps', 'StreamDeck', 'PIL', 'paramiko'],
    'includes': ['src.streamdeck_controller', 'src.button_manager', 'src.config_loader', 
                 'src.command_executor', 'src.image_manager', 'src.keyboard_parser',
                 'src.notification_helper', 'src.config_watcher'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)