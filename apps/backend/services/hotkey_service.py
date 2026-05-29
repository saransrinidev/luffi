import keyboard
import logging
import httpx
import winsound
import threading

from services.clipboard_service import ClipboardService
from services.popup_service import PopupService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HotkeyService:
    def __init__(self):
        self.clipboard_service = ClipboardService()
        self.hotkey = settings.hotkey

    def start(self):
        """Register global hotkey and block."""
        logger.info(f"Registering hotkey: {self.hotkey}")
        keyboard.add_hotkey(self.hotkey, self._on_hotkey)
        winsound.Beep(1000, 200)
        print("\n✅ NAP is ready! Press Ctrl+; to capture text.\n")
        keyboard.wait()

    def _on_hotkey(self):
        """Handle hotkey press: capture text and trigger explain."""
        winsound.Beep(1500, 100)
        print("🔑 Hotkey triggered! Capturing text...")
        logger.info("Hotkey triggered")

        text = self.clipboard_service.capture_selected_text()

        if not text:
            winsound.Beep(400, 200)
            print("⚠️  No text captured from clipboard")
            return

        print(f"📋 Captured: {text[:80]}...")

        # Show loading popup immediately
        PopupService.show("⏳ Thinking...", title="NAP")

        # Call LLM in background thread
        thread = threading.Thread(target=self._get_explanation, args=(text,), daemon=True)
        thread.start()

    def _get_explanation(self, text: str):
        """Call LLM and show result in popup."""
        try:
            response = httpx.post(
                f"http://{settings.host}:{settings.port}/explain",
                json={"text": text},
                timeout=60.0,
            )
            if response.status_code == 200:
                data = response.json()
                explanation = data["explanation"]
                model = data["model_used"]
                print(f"✅ Done ({model})\n")
                winsound.Beep(2000, 100)
                PopupService.show(explanation, title=f"NAP · {model}")
            else:
                winsound.Beep(400, 300)
                PopupService.show(f"❌ Error: API returned {response.status_code}")
        except Exception as e:
            winsound.Beep(400, 300)
            PopupService.show(f"❌ Error: {e}")
            logger.error(f"LLM call failed: {e}")
