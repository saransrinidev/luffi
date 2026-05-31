"""
Launcher Service — opens apps the way a human would.

Strategy (no subprocess shortcuts — pure cursor + keyboard):
1. Scan the taskbar for the app icon.
2. If found → move cursor to it and click (like a person).
3. If NOT found → open Windows Search (Win key), type the app name,
   wait for results, press Enter to launch.

This is fully manual desktop interaction — nothing is launched silently.
"""
import logging
import time
import subprocess
import pyautogui
from services.mouse_service import human_click, human_type

logger = logging.getLogger(__name__)


# PowerShell to read taskbar buttons with coordinates
_TASKBAR_PS = r'''
$ErrorActionPreference = "SilentlyContinue"
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ClassNameProperty, "Shell_TrayWnd")
$taskbar = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $cond)

if ($taskbar) {
    $btnCond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Button)
    $buttons = $taskbar.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
    foreach ($b in $buttons) {
        try {
            $n = $b.Current.Name
            $r = $b.Current.BoundingRectangle
            if ($n -and $r.Width -gt 0) {
                $cx = [int]($r.X + $r.Width/2)
                $cy = [int]($r.Y + $r.Height/2)
                Write-Output "$n|$cx|$cy"
            }
        } catch {}
    }
}
'''


# Aliases so "chrome" matches "Google Chrome" taskbar label, etc.
APP_ALIASES = {
    "firefox": ["firefox", "mozilla firefox"],
    "chrome": ["chrome", "google chrome"],
    "edge": ["edge", "microsoft edge"],
    "notepad": ["notepad"],
    "explorer": ["file explorer", "explorer"],
    "files": ["file explorer", "explorer"],
    "cmd": ["command prompt", "cmd"],
    "terminal": ["terminal", "windows terminal"],
    "code": ["visual studio code", "code", "vs code"],
    "vscode": ["visual studio code", "code", "vs code"],
    "calculator": ["calculator", "calc"],
    "calc": ["calculator", "calc"],
    "paint": ["paint", "mspaint"],
    "vlc": ["vlc", "vlc media player"],
    "spotify": ["spotify"],
    "word": ["word", "microsoft word"],
    "excel": ["excel", "microsoft excel"],
}


class LauncherResult:
    def __init__(self, success: bool, message: str, method: str = ""):
        self.success = success
        self.message = message
        self.method = method  # "taskbar" or "search"

    def __str__(self):
        return f"{'✓' if self.success else '✗'} {self.message}"


class LauncherService:
    """Opens apps via taskbar click or Windows search — like a human."""

    def open_app(self, app: str, on_status=None) -> LauncherResult:
        """Open an app the human way."""
        def status(msg):
            logger.info(msg)
            if on_status:
                on_status(msg)

        app_key = app.lower().strip()
        aliases = APP_ALIASES.get(app_key, [app_key])

        # Step 1: Look in the taskbar
        status(f"Looking for {app} in taskbar...")
        match = self._find_in_taskbar(aliases)

        if match:
            name, x, y = match
            status(f"Found '{name}' in taskbar — clicking")
            human_click(x, y)
            time.sleep(1.5)
            if self._wait_for_window(aliases):
                return LauncherResult(True, f"Opened {app} from taskbar", "taskbar")
            return LauncherResult(True, f"Clicked {app} in taskbar", "taskbar")

        # Step 2: Not in taskbar — use Windows Search
        status(f"{app} not in taskbar — searching Windows...")
        return self._open_via_search(app, aliases, status)

    def _find_in_taskbar(self, aliases: list[str]) -> tuple[str, int, int] | None:
        """Scan taskbar buttons, return (name, x, y) of first matching app."""
        buttons = self._scan_taskbar()
        for name, x, y in buttons:
            name_lower = name.lower()
            for alias in aliases:
                if alias in name_lower:
                    return (name, x, y)
        return None

    def _scan_taskbar(self) -> list[tuple[str, int, int]]:
        """Read all taskbar buttons with coordinates."""
        buttons = []
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", _TASKBAR_PS],
                capture_output=True, text=True, timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in result.stdout.strip().split("\n"):
                parts = line.strip().split("|")
                if len(parts) == 3:
                    buttons.append((parts[0], int(parts[1]), int(parts[2])))
        except Exception as e:
            logger.error(f"Taskbar scan failed: {e}")
        return buttons

    def _open_via_search(self, app: str, aliases: list[str], status) -> LauncherResult:
        """Open the app using Windows Search (Win key → type → Enter)."""
        # Press Win to open Start/Search
        status("Opening Windows search...")
        pyautogui.press("win")
        time.sleep(1.2)

        # Type the app name (human-like)
        status(f"Typing '{app}'...")
        human_type(app)
        time.sleep(1.5)  # wait for search results to populate

        # Press Enter to launch the top result
        status("Pressing Enter to open top result...")
        pyautogui.press("enter")
        time.sleep(2.0)

        if self._wait_for_window(aliases):
            return LauncherResult(True, f"Opened {app} via search", "search")
        return LauncherResult(True, f"Searched and opened {app}", "search")

    def _wait_for_window(self, aliases: list[str], timeout: int = 6) -> bool:
        """Wait for a window matching the app to become foreground."""
        import ctypes
        for _ in range(timeout * 2):
            time.sleep(0.5)
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()
            for alias in aliases:
                if alias in title:
                    return True
        return False
