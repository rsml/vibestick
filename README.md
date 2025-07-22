# 🔥 Vibestick

A macOS menubar app for StreamDeck Dual Control - control multiple computers with a single StreamDeck.

![Vibestick Icon](assets/vibestick-icon.png)

## Features

- 🎮 **Menubar Control**: Simple menubar interface for StreamDeck management
- 🔄 **Auto-Start**: Launches automatically on login
- 🖥️ **Dual Computer Support**: Control laptop and desktop from one StreamDeck
- 🎯 **Multiple Modes**: Terminal, Simulator, and Fork (Git) modes
- 🔧 **Easy Reload**: Restart the controller without quitting the app
- 📊 **Status Monitoring**: See connection status in the menubar

## Requirements

- macOS 10.15 or later
- Python 3.8+
- [StreamDeck](https://www.elgato.com/en/stream-deck) hardware
- [python-streamdeck](https://github.com/abcminiuser/python-elgato-streamdeck) library
- [rumps](https://github.com/jaredks/rumps) for menubar functionality

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vibestick.git
cd vibestick
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Build the app:
```bash
./build_app.sh
```

4. Install the app:
```bash
./install.sh
```

### Pre-built App

Download the latest release from the [Releases](https://github.com/yourusername/vibestick/releases) page and drag `Vibestick.app` to your Applications folder.

## Usage

Once installed, Vibestick will:
- Start automatically when you log in
- Show a joystick icon in your menubar
- Run the StreamDeck controller in the background

### Menu Options

- **Status**: Shows current connection status
- **Reload**: Restarts the StreamDeck controller
- **Show Logs**: Opens Console.app for debugging
- **Quit**: Stops Vibestick and the controller

## Configuration

The app looks for configuration files in the `config/` directory within the app location.

**Important: Before first run, create a `config/mode.json` file:**

```bash
cd /path/to/vibestick
cp config/terminal-mode.json config/mode.json
```

Available mode templates:
- `terminal-mode.json` - Terminal/development commands
- `simulator-mode.json` - iOS Simulator controls  
- `fork-mode.json` - Fork git client shortcuts
- `overview.json` - Overview/navigation mode

Configuration files:
```
config/
├── mode.json          # Current mode (create from template)
├── computers.json     # Computer connection settings
├── terminal-mode.json # Terminal mode template
├── simulator-mode.json # Simulator mode template
├── fork-mode.json     # Fork mode template
└── overview.json      # Overview mode template
```

### Computer Configuration

Edit `computers.json` to set up your computers:

```json
{
  "laptop": {
    "address": "192.168.0.5",
    "betterTouchToolSharedSecret": "your-secret-here",
    "betterTouchToolPort": 61708
  },
  "desktop": {
    "address": "192.168.0.6",
    "betterTouchToolSharedSecret": "your-secret-here",
    "betterTouchToolPort": 61708
  }
}
```

## Building from Source

### Requirements

- Python 3.8+
- py2app
- All dependencies from requirements.txt

### Build Steps

1. Install build dependencies:
```bash
pip install py2app
```

2. Run the build script:
```bash
./build_app.sh
```

3. The app will be created in `dist/Vibestick.app`

## Development

### Running without Building

```bash
python vibestick.py
```

### Project Structure

```
vibestick/
├── vibestick.py          # Main menubar app
├── setup.py              # py2app configuration
├── build_app.sh          # Build script
├── install.sh            # Installation script
├── uninstall.sh          # Uninstall script
├── com.rossthedev.vibestick.plist  # LaunchAgent config
├── assets/
│   └── vibestick-icon.png  # Menubar icon
└── requirements.txt      # Python dependencies
```

## Troubleshooting

### App doesn't start
- Check Console.app for error messages
- Ensure StreamDeck is connected
- Verify Python dependencies are installed

### StreamDeck not detected
- Check USB connection
- Install HIDapi: `brew install hidapi`
- Grant necessary permissions in System Preferences

### Logs
Logs are written to:
- `/tmp/vibestick.out` - Standard output
- `/tmp/vibestick.err` - Error output

## Uninstalling

Run the uninstall script:
```bash
./uninstall.sh
```

Or manually:
1. Remove from Applications: `rm -rf /Applications/Vibestick.app`
2. Remove LaunchAgent: `rm ~/Library/LaunchAgents/com.rossthedev.vibestick.plist`
3. Remove support files: `rm -rf ~/Library/Application Support/Vibestick`

## License

MIT License - see LICENSE file for details

## Credits

- Built with [rumps](https://github.com/jaredks/rumps)
- StreamDeck control via [python-elgato-streamdeck](https://github.com/abcminiuser/python-elgato-streamdeck)
- Part of the [StreamDeck Dual Control](https://github.com/yourusername/streamdeck-dual-control) project

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- Open an issue on [GitHub](https://github.com/yourusername/vibestick/issues)
- Check the [Wiki](https://github.com/yourusername/vibestick/wiki) for documentation