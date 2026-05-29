import keyboard
import logging
import httpx
import winsound
import threading

from services.clipboard_service import ClipboardService
from services.popup_service import PopupService
from services.prompt_service import PromptService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HotkeyService:
    def __init__(self):
        self.clipboard_service = ClipboardService()
        self.prompt_service = PromptService()

    def start(self):
        """Register all mode hotkeys and block."""
        modes = self.prompt_service.get_modes()

        for mode, info in modes.items():
            hotkey = info["hotkey"]
            label = info["label"]
            keyboard.add_hotkey(hotkey, self._on_hotkey, args=(mode, label))
            logger.info(f"Registered: {hotkey} → {label}")

        winsound.Beep(1000, 200)
        print("\n✅ NAP is ready!\n")
        print("   Hotkeys:")
        for mode, info in modes.items():
            print(f"   {info['hotkey']:20s} → {info['label']}")
        print()
        keyboard.wait()

    def _on_hotkey(self, mode: str, label: str):
        """Handle hotkey press for a specific mode."""
        winsound.Beep(1500, 100)
        print(f"🔑 [{label}] Hotkey triggered!")
        logger.info(f"Hotkey triggered: {mode}")

        text = self.clipboard_service.capture_selected_text()

        if not text:
            winsound.Beep(400, 200)
            print("⚠️  No text captured")
            return

        print(f"📋 Captured: {text[:80]}...")
        PopupService.show(f"⏳ {label}...\n\nThinking...", title=f"NAP · {label}")

        thread = threading.Thread(
            target=self._get_explanation, args=(text, mode, label), daemon=True
        )
        thread.start()

    def _get_explanation(self, text: str, mode: str, label: str):
        """Call LLM and show result in popup."""
        try:
            response = httpx.post(
                f"http://{settings.host}:{settings.port}/explain",
                json={"text": text, "mode": mode},
                timeout=60.0,
            )
            if response.status_code == 200:
                data = response.json()
                explanation = data["explanation"]
                model = data["model_used"]
                print(f"✅ [{label}] Done ({model})\n")
                winsound.Beep(2000, 100)
                PopupService.show(explanation, title=f"NAP · {label} · {model}")
            else:
                winsound.Beep(400, 300)
                PopupService.show(f"❌ Error: API returned {response.status_code}")
        except Exception as e:
            winsound.Beep(400, 300)
            PopupService.show(f"❌ Error: {e}")
            logger.error(f"LLM call failed: {e}")
