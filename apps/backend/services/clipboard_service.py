import pyautogui
import pyperclip
import time
import logging

logger = logging.getLogger(__name__)


class ClipboardService:
    def __init__(self):
        self.copy_delay = 0.1  # seconds to wait after Ctrl+C

    def capture_selected_text(self) -> str | None:
        """Simulate Ctrl+C and read clipboard content."""
        try:
            # Save current clipboard
            old_clipboard = pyperclip.paste()

            # Clear clipboard
            pyperclip.copy("")

            # Simulate Ctrl+C
            pyautogui.hotkey("ctrl", "c")
            time.sleep(self.copy_delay)

            # Read new clipboard content
            text = pyperclip.paste()

            # Restore old clipboard if nothing was captured
            if not text:
                pyperclip.copy(old_clipboard)
                return None

            return text.strip()

        except Exception as e:
            logger.error(f"Clipboard capture failed: {e}")
            return None
