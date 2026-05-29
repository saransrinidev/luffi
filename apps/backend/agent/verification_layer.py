"""
Layer 7: Verification Loop
After execution, checks if the action succeeded.
"""
import logging
import time
import ctypes
from services.desktop_service import DesktopService

logger = logging.getLogger(__name__)


class VerificationResult:
    """Result of verification check."""

    def __init__(self, passed: bool, checks: dict):
        self.passed = passed
        self.checks = checks

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        details = ", ".join(f"{k}={v}" for k, v in self.checks.items())
        return f"[{status}] {details}"


class VerificationLayer:
    """Verifies that actions completed successfully."""

    def __init__(self):
        self.desktop = DesktopService()

    def verify_launch(self, app_name: str) -> VerificationResult:
        """Verify an app launched and is foreground."""
        time.sleep(0.5)
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.lower()

        app_visible = app_name.lower() in title
        checks = {
            "window_title": buf.value[:40],
            "app_in_title": app_visible,
        }

        return VerificationResult(passed=app_visible, checks=checks)

    def verify_focus_changed(self, expected_type: str = None) -> VerificationResult:
        """Verify that focus moved to expected element type."""
        state = self.desktop.refresh()
        checks = {
            "foreground": state.foreground_app,
            "elements": len(state.elements),
        }

        # Check if any element of expected type is present
        if expected_type:
            has_type = any(el.control_type == expected_type for el in state.elements)
            checks["has_expected_type"] = has_type
            return VerificationResult(passed=has_type, checks=checks)

        return VerificationResult(passed=True, checks=checks)

    def verify_window_changed(self, previous_title: str) -> VerificationResult:
        """Verify the window title changed (e.g., page navigated)."""
        time.sleep(1)
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        current_title = buf.value

        changed = current_title != previous_title
        checks = {
            "previous": previous_title[:30],
            "current": current_title[:30],
            "changed": changed,
        }

        return VerificationResult(passed=changed, checks=checks)
