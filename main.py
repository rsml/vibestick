#!/usr/bin/env python3
"""
Stub main.py for Vibestick
This should be replaced with your actual StreamDeck controller
"""

import time
import sys

print("StreamDeck controller started by Vibestick")
print("This is a stub - replace with your actual controller")

# Keep running until terminated
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStreamDeck controller stopped")
    sys.exit(0)