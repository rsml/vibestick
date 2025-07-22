#!/bin/bash
# Build script for Vibestick.app

echo "Building Vibestick.app..."

# Clean previous builds
rm -rf build dist

# Create ICNS from PNG (if not exists)
if [ ! -f "assets/vibestick-icon.icns" ]; then
    echo "Creating ICNS icon..."
    # We'll need to create this manually or use iconutil
    # For now, we'll skip the icon
    touch assets/vibestick-icon.icns
fi

# Install requirements
pip install py2app rumps

# Build the app
python setup.py py2app

# Check if build succeeded
if [ -d "dist/Vibestick.app" ]; then
    echo "✅ Build successful!"
    echo "📍 App location: dist/Vibestick.app"
    echo ""
    echo "To install:"
    echo "  cp -r dist/Vibestick.app /Applications/"
    echo ""
    echo "To run:"
    echo "  open dist/Vibestick.app"
else
    echo "❌ Build failed!"
    exit 1
fi