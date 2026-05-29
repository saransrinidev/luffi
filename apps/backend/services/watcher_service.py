import time
import threading
import logging
import pyperclip

logger = logging.getLogger(__name__)


class ClipboardWatcher:
    """Watches clipboard for changes and auto-triggers explanation."""

    def __init__(self, callback=None):
        self.callback = callback
        self.running = False
        self.last_content = ""
        self._thread = None

    def start(self):
        """Start watching clipboard in background."""
        self.running = True
        self.last_content = pyperclip.paste()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()
        logger.info("Clipboard watcher started")
        print("👁️  Clipboard watcher ON — copies will auto-explain")

    def stop(self):
        """Stop watching."""
        self.running = False
        logger.info("Clipboard watcher stopped")
        print("👁️  Clipboard watcher OFF")

    def toggle(self) -> bool:
        """Toggle watcher on/off. Returns new state."""
        if self.running:
            self.stop()
            return False
        else:
            self.start()
            return True

    def _watch(self):
        """Poll clipboard every 500ms for changes."""
        while self.running:
            try:
                current = pyperclip.paste()
                if current != self.last_content and current.strip():
                    self.last_content = current
                    if self.callback:
                        self.callback(current)
            except Exception as e:
                logger.error(f"Watcher error: {e}")
            time.sleep(0.5)
