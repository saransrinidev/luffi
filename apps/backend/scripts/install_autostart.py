"""Add Luffi to Windows startup."""
import os
import sys
import winreg

APP_NAME = "Luffi"
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
PYTHON_PATH = sys.executable


def add_to_startup():
    """Add Luffi to Windows registry startup."""
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    command = f'"{PYTHON_PATH}" "{SCRIPT_PATH}"'
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
    winreg.CloseKey(key)
    print(f"✅ Luffi added to startup: {command}")


def remove_from_startup():
    """Remove Luffi from Windows registry startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        print("✅ Luffi removed from startup")
    except FileNotFoundError:
        print("Luffi was not in startup")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "remove":
        remove_from_startup()
    else:
        add_to_startup()
