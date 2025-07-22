# 🚀 Vibestick Quick Start

## 1. Download and Install

### Option A: Download Pre-built App
1. Go to [Releases](https://github.com/yourusername/vibestick/releases)
2. Download `Vibestick.dmg`
3. Open the DMG and drag Vibestick to Applications
4. Open Vibestick from Applications

### Option B: Build from Source
```bash
git clone https://github.com/yourusername/vibestick.git
cd vibestick
pip install -r requirements.txt
./build_app.sh
./install.sh
```

## 2. First Run

When you first run Vibestick:
1. You'll see a joystick icon in your menubar
2. The app will show "Status: Starting..."
3. If you have a StreamDeck connected, it will show "Status: Running"

## 3. Basic Usage

Click the menubar icon to see options:
- **Status**: Shows if StreamDeck is connected
- **Reload**: Restart the StreamDeck controller
- **Show Logs**: Open Console for debugging
- **Quit**: Stop Vibestick

## 4. Connect Your StreamDeck Controller

Replace the stub `main.py` with your actual StreamDeck controller:

```bash
# In the Vibestick app bundle:
/Applications/Vibestick.app/Contents/Resources/main.py
```

Or link to your existing controller:
```bash
ln -sf /path/to/your/streamdeck/main.py /Applications/Vibestick.app/Contents/Resources/main.py
```

## 5. Auto-Start Setup

Vibestick automatically installs a LaunchAgent for auto-start. To verify:
```bash
launchctl list | grep vibestick
```

To disable auto-start:
```bash
launchctl unload ~/Library/LaunchAgents/com.rossthedev.vibestick.plist
```

## 6. Troubleshooting

### Vibestick won't start
- Check Console.app for errors
- Ensure you have Python 3.8+ installed
- Try running from terminal: `/Applications/Vibestick.app/Contents/MacOS/Vibestick`

### StreamDeck not detected
- Make sure your StreamDeck controller (`main.py`) is working
- Check USB connection
- Look at logs in `/tmp/vibestick.out`

### Need Help?
- Check the full [README](README.md)
- Open an [issue](https://github.com/yourusername/vibestick/issues)