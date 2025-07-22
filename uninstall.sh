#!/bin/bash
# Uninstall script for Vibestick

echo "🗑️  Uninstalling Vibestick..."

# Unload LaunchAgent
echo "Stopping auto-startup..."
launchctl unload ~/Library/LaunchAgents/com.rossthedev.vibestick.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.rossthedev.vibestick.plist

# Quit the app if running
echo "Quitting Vibestick..."
osascript -e 'quit app "Vibestick"' 2>/dev/null

# Remove from Applications
echo "Removing from Applications..."
rm -rf /Applications/Vibestick.app

echo "✅ Uninstall complete!"