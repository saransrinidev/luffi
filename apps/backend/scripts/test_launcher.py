"""Test the human-like launcher. Pass app name as arg.
Example: python scripts/test_launcher.py firefox
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.launcher_service import LauncherService

app = sys.argv[1] if len(sys.argv) > 1 else "notepad"

print(f"Testing launcher for: {app}\n")

launcher = LauncherService()

# First just show what's in the taskbar
print("=== Taskbar scan ===")
for name, x, y in launcher._scan_taskbar():
    print(f"  {name:45s} ({x}, {y})")

print(f"\n=== Opening '{app}' (3 sec delay) ===")
import time
time.sleep(3)

result = launcher.open_app(app, on_status=lambda m: print(f"  • {m}"))
print(f"\nResult: {result}  [method: {result.method}]")
