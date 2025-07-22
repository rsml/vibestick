#!/bin/bash
# Install script for Vibestick

echo "🔥 Installing Vibestick..."

# Check if Vibestick.app exists
if [ ! -d "dist/Vibestick.app" ]; then
    echo "❌ Vibestick.app not found. Please run ./build_app.sh first"
    exit 1
fi

# Copy app to Applications
echo "📦 Installing app to /Applications..."
cp -r dist/Vibestick.app /Applications/

# Install LaunchAgent for auto-startup
echo "🚀 Setting up auto-startup..."
cp com.rossthedev.vibestick.plist ~/Library/LaunchAgents/

# Load the LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.rossthedev.vibestick.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.rossthedev.vibestick.plist

echo "✅ Installation complete!"
echo ""
echo "Vibestick will now:"
echo "  • Start automatically on login"
echo "  • Show in your menubar with a joystick icon"
echo "  • Run the StreamDeck controller"
echo ""
echo "To start now: open /Applications/Vibestick.app"
echo "To uninstall: ./uninstall.sh"