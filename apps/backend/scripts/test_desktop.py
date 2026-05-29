"""Test script — run this to see what the desktop service captures.
Open Calculator first, then run this to see button names.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.desktop_service import DesktopService

print("Testing desktop state capture...\n")
print("(Make sure Calculator is the ACTIVE window!)\n")

import time
time.sleep(2)  # Give you time to click calculator

desktop = DesktopService()
state = desktop.get_state(force_refresh=True)

print(state.to_prompt())
print(f"\n--- Total elements found: {len(state.elements)} ---")

# Show only buttons
print("\n--- BUTTONS only ---")
for el in state.elements:
    if el.control_type == "Button":
        print(f"  \"{el.name}\" at ({el.x}, {el.y})")
