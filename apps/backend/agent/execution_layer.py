"""
Layer 6: Execution Layer
Executes actions using PyAutoGUI with human-like mouse movement.
"""
import logging
import time
import subprocess
import pyautogui
from services.mouse_service import human_click, human_move
from agent.template_engine import ActionStep

logger = logging.getLogger(__name__)

APP_MAP = {
    "firefox": "firefox",
    "chrome": "chrome",
    "edge": "msedge",
    "notepad": "notepad",
    "explorer": "explorer",
    "cmd": "cmd",
    "terminal": "wt",
    "code": "code",
    "vscode": "code",
    "calc": "calc",
    "calculator": "calc",
    "paint": "mspaint",
    "browser": "firefox",
}


class ExecutionResult:
    """Result of executing an action."""

    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message

    def __str__(self):
        icon = "✓" if self.success else "✗"
        return f"{icon} {self.message}"


class ExecutionLayer:
    """Executes action steps."""

    def __init__(self):
        from services.desktop_service import DesktopService
        self.desktop = DesktopService()

    def execute_step(self, step: ActionStep) -> ExecutionResult:
        """Execute a single action step."""
        action = step.action
        params = step.params

        try:
            if action == "launch":
                return self._launch(params.get("app", ""))

            elif action == "click":
                x = params.get("x", 0)
                y = params.get("y", 0)
                human_click(int(x), int(y))
                return ExecutionResult(True, f"clicked ({x}, {y})")

            elif action == "click_button":
                name = params.get("name", "")
                fallback_key = params.get("fallback_key")
                return self._click_button_by_name(name, fallback_key)

            elif action == "type":
                text = params.get("text", "")
                time.sleep(0.1)
                if not text.isascii():
                    import pyperclip
                    pyperclip.copy(text)
                    pyautogui.hotkey("ctrl", "v")
                else:
                    pyautogui.typewrite(text, interval=0.02)
                return ExecutionResult(True, f"typed '{text[:30]}'")

            elif action == "key":
                keys = params.get("keys", "")
                if "+" in keys:
                    parts = [k.strip() for k in keys.split("+")]
                    pyautogui.hotkey(*parts)
                else:
                    pyautogui.press(keys)
                return ExecutionResult(True, f"pressed {keys}")

            elif action == "wait":
                secs = float(params.get("seconds", 1))
                time.sleep(secs)
                return ExecutionResult(True, f"waited {secs}s")

            elif action == "scroll":
                direction = params.get("direction", "down")
                amount = int(params.get("amount", 3))
                clicks = amount if direction == "up" else -amount
                pyautogui.scroll(clicks)
                return ExecutionResult(True, f"scrolled {direction}")

            elif action == "done":
                return ExecutionResult(True, params.get("message", "done"))

            else:
                return ExecutionResult(False, f"unknown action: {action}")

        except Exception as e:
            logger.error(f"Execution error: {e}")
            return ExecutionResult(False, f"error: {e}")

    def _click_button_by_name(self, name: str, fallback_key: str = None) -> ExecutionResult:
        """Find a button by name in UI tree and click it with cursor.
        Falls back to keypress if button not found."""
        state = self.desktop.refresh()
        name_lower = name.lower()

        # Exact match
        for el in state.elements:
            if el.name.lower() == name_lower:
                human_click(el.x, el.y)
                return ExecutionResult(True, f"clicked '{el.name}' at ({el.x}, {el.y})")

        # Partial match
        for el in state.elements:
            if name_lower in el.name.lower() or el.name.lower() in name_lower:
                human_click(el.x, el.y)
                return ExecutionResult(True, f"clicked '{el.name}' at ({el.x}, {el.y})")

        # Fallback to keypress
        if fallback_key:
            if fallback_key == "+":
                pyautogui.press("add")
            elif fallback_key == "-":
                pyautogui.press("subtract")
            elif fallback_key == "*":
                pyautogui.press("multiply")
            elif fallback_key == "/":
                pyautogui.press("divide")
            elif fallback_key == "=":
                pyautogui.press("enter")
            else:
                pyautogui.press(fallback_key)
            return ExecutionResult(True, f"key fallback '{fallback_key}' (button '{name}' not found)")

        return ExecutionResult(False, f"button '{name}' not found")

    def _launch(self, app: str) -> ExecutionResult:
        """Launch an application and wait for it."""
        import ctypes

        app_lower = app.lower().strip()
        exe = APP_MAP.get(app_lower, app_lower)

        try:
            subprocess.Popen(f"start {exe}", shell=True)

            # Wait for foreground window to change
            for _ in range(12):
                time.sleep(0.5)
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if app_lower in title or exe.lower() in title:
                    time.sleep(0.5)
                    return ExecutionResult(True, f"launched {app}")

            time.sleep(1)
            return ExecutionResult(True, f"launched {app} (waited)")

        except Exception as e:
            return ExecutionResult(False, f"launch failed: {e}")

    def execute_sequence(self, steps: list[ActionStep], on_step=None) -> list[ExecutionResult]:
        """Execute a sequence of steps."""
        results = []
        for i, step in enumerate(steps):
            if on_step:
                on_step(i, step)
            result = self.execute_step(step)
            results.append(result)
            logger.info(f"  Step {i+1}: {result}")

            if not result.success:
                break
            if step.action == "done":
                break

        return results
