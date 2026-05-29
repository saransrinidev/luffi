"""
Desktop Perception Service — reads the Windows UI element tree.
Same approach as Yuki: UIAutomation API to get all interactive elements
with their names, types, and exact coordinates.
"""
import logging
import ctypes
import ctypes.wintypes
import subprocess
import time
import pyautogui

logger = logging.getLogger(__name__)


class UIElement:
    """Represents a single UI element on screen."""

    def __init__(self, label: int, app_name: str, control_type: str,
                 name: str, x: int, y: int):
        self.label = label
        self.app_name = app_name
        self.control_type = control_type
        self.name = name
        self.x = x
        self.y = y

    def __str__(self):
        return (f"[{self.label}] {self.control_type} \"{self.name}\" "
                f"at ({self.x}, {self.y}) — {self.app_name}")


class DesktopState:
    """Complete snapshot of the current desktop state."""

    def __init__(self):
        self.cursor_x = 0
        self.cursor_y = 0
        self.foreground_app = ""
        self.foreground_title = ""
        self.screen_width = 0
        self.screen_height = 0
        self.elements: list[UIElement] = []
        self.timestamp = 0.0

    def to_prompt(self) -> str:
        """Format state as text for the LLM."""
        lines = []
        lines.append(f"Screen: {self.screen_width}x{self.screen_height}")
        lines.append(f"Cursor: ({self.cursor_x}, {self.cursor_y})")
        lines.append(f"Active Window: {self.foreground_app} — {self.foreground_title}")
        lines.append(f"Elements ({len(self.elements)}):")

        for el in self.elements:
            lines.append(str(el))

        return "\n".join(lines)


class DesktopService:
    """
    Captures the current desktop state using Windows UIAutomation.
    Provides element coordinates for the agent to click/type.
    """

    # PowerShell script to read UI elements
    PS_SCRIPT = '''
$ErrorActionPreference = "SilentlyContinue"
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# Get foreground window
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
}
"@

$hwnd = [Win32]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[Win32]::GetWindowText($hwnd, $sb, 256) | Out-Null
$windowTitle = $sb.ToString()

# Get the automation element for foreground window
$ae = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
$appName = ""
if ($ae) { $appName = $ae.Current.Name }

Write-Output "WINDOW:$appName|$windowTitle"

# Get interactive elements
$condition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::IsEnabledProperty, $true
)

$elements = $ae.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)

$count = 0
foreach ($el in $elements) {
    if ($count -ge 20) { break }
    try {
        $name = $el.Current.Name
        $ctrlType = $el.Current.ControlType.ProgrammaticName -replace "ControlType.", ""
        $rect = $el.Current.BoundingRectangle

        # Skip invisible or tiny elements
        if ($rect.Width -lt 5 -or $rect.Height -lt 5) { continue }
        if ([string]::IsNullOrWhiteSpace($name)) { continue }

        # Only interactive types
        $interactive = @("Button","Edit","ComboBox","CheckBox","RadioButton",
                        "MenuItem","Link","Tab","TabItem","ListItem","TreeItem")
        if ($interactive -notcontains $ctrlType) { continue }

        $cx = [int]($rect.X + $rect.Width / 2)
        $cy = [int]($rect.Y + $rect.Height / 2)

        # Skip offscreen
        if ($cx -lt 0 -or $cy -lt 0 -or $cx -gt 3000 -or $cy -gt 2000) { continue }

        Write-Output "EL:$count|$appName|$ctrlType|$name|$cx|$cy"
        $count++
    } catch {}
}
'''

    def __init__(self):
        self._cache: DesktopState | None = None
        self._cache_time = 0.0
        self._cache_ttl = 1.5  # seconds

    def get_state(self, force_refresh: bool = False) -> DesktopState:
        """Get current desktop state. Uses cache if fresh enough."""
        now = time.time()
        if not force_refresh and self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        state = DesktopState()
        state.timestamp = now

        # Screen resolution
        user32 = ctypes.windll.user32
        state.screen_width = user32.GetSystemMetrics(0)
        state.screen_height = user32.GetSystemMetrics(1)

        # Cursor position
        state.cursor_x, state.cursor_y = pyautogui.position()

        # Get UI elements via PowerShell
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", self.PS_SCRIPT],
                capture_output=True, text=True, timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            label_counter = 0
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.startswith("WINDOW:"):
                    parts = line[7:].split("|", 1)
                    state.foreground_app = parts[0] if parts else ""
                    state.foreground_title = parts[1] if len(parts) > 1 else ""

                elif line.startswith("EL:"):
                    parts = line[3:].split("|")
                    if len(parts) >= 6:
                        el = UIElement(
                            label=label_counter,
                            app_name=parts[1],
                            control_type=parts[2],
                            name=parts[3],
                            x=int(parts[4]),
                            y=int(parts[5]),
                        )
                        state.elements.append(el)
                        label_counter += 1

        except subprocess.TimeoutExpired:
            logger.warning("UI scan timed out")
            state.foreground_app = "unknown"
            state.foreground_title = "scan timed out"
        except Exception as e:
            logger.error(f"Desktop state capture failed: {e}")

        self._cache = state
        self._cache_time = now
        return state

    def refresh(self) -> DesktopState:
        """Force refresh the desktop state."""
        return self.get_state(force_refresh=True)
