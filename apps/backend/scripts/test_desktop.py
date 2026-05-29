"""Test script — run this to see what the desktop service captures."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.desktop_service import DesktopService

print("Testing desktop state capture...\n")
desktop = DesktopService()
state = desktop.get_state(force_refresh=True)

print(state.to_prompt())
print(f"\n--- Total elements found: {len(state.elements)} ---")
