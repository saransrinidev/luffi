import logging
import subprocess
import json
import ctypes
from ctypes import wintypes

logger = logging.getLogger(__name__)


class ScreenService:
    """
    Reads the Windows UI element tree for the active window.
    Gives the LLM structured data about what's on screen with coordinates.
    """

    @staticmethod
    def get_active_window_info() -> dict:
        """Get active window title and process."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return {"title": buf.value, "hwnd": hwnd}
        except Exception as e:
            return {"title": "unknown", "hwnd": 0}

    @staticmethod
    def get_screen_resolution() -> tuple[int, int]:
        """Get screen resolution."""
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    @staticmethod
    def get_ui_elements() -> str:
        """
        Get UI elements of the active window using PowerShell + UIAutomation.
        Returns a simplified text list of clickable elements with coordinates.
        """
        # Use a lightweight PowerShell script to read UI elements
        ps_script = '''
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::FocusedElement
if (-not $root) { $root = [System.Windows.Automation.AutomationElement]::RootElement }

# Get the active window
$hwnd = (Get-Process | Where-Object {$_.MainWindowHandle -ne 0} | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object -First 1).MainWindowHandle
$window = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$hwnd) 2>$null
if (-not $window) { $window = $root }

$condition = [System.Windows.Automation.Condition]::TrueCondition
$elements = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)

$results = @()
$count = 0
foreach ($el in $elements) {
    if ($count -ge 30) { break }
    try {
        $name = $el.Current.Name
        $type = $el.Current.ControlType.ProgrammaticName
        $rect = $el.Current.BoundingRectangle
        if ($name -and $rect.Width -gt 0 -and $rect.Height -gt 0) {
            $cx = [int]($rect.X + $rect.Width/2)
            $cy = [int]($rect.Y + $rect.Height/2)
            $shortType = $type -replace "ControlType.", ""
            $results += "[$count] $shortType `"$name`" at ($cx, $cy)"
            $count++
        }
    } catch {}
}
$results -join "`n"
'''
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            if output:
                return output
            return "[No UI elements detected]"
        except subprocess.TimeoutExpired:
            return "[UI scan timed out]"
        except Exception as e:
            logger.error(f"UI element scan failed: {e}")
            return "[UI scan failed]"

    @staticmethod
    def get_screen_state() -> str:
        """Get full screen state as text for the LLM."""
        window = ScreenService.get_active_window_info()
        res = ScreenService.get_screen_resolution()
        elements = ScreenService.get_ui_elements()

        state = f"Screen: {res[0]}x{res[1]}\n"
        state += f"Active window: {window['title']}\n"
        state += f"UI Elements:\n{elements}"
        return state
