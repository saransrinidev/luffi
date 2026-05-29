import keyboard
import logging
import httpx
import winsound
import threading

from services.clipboard_service import ClipboardService
from services.popup_service import PopupService
from services.input_popup_service import InputPopupService
from services.command_service import CommandService
from services.agent_service import AgentService
from services.prompt_service import PromptService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

INPUT_HOTKEY = "ctrl+shift+;"


class HotkeyService:
    def __init__(self):
        self.clipboard_service = ClipboardService()
        self.prompt_service = PromptService()
        self.command_service = CommandService()
        self.agent_service = AgentService()

    def start(self):
        """Register all mode hotkeys and block."""
        modes = self.prompt_service.get_modes()

        for mode, info in modes.items():
            hotkey = info["hotkey"]
            label = info["label"]
            keyboard.add_hotkey(hotkey, self._on_hotkey, args=(mode, label))
            logger.info(f"Registered: {hotkey} → {label}")

        # Register input box hotkey
        keyboard.add_hotkey(INPUT_HOTKEY, self._on_input_hotkey)
        logger.info(f"Registered: {INPUT_HOTKEY} → Ask (Input Box)")

        winsound.Beep(1000, 200)
        print("\n✅ Luffi is ready!\n")
        print("   Hotkeys:")
        for mode, info in modes.items():
            print(f"   {info['hotkey']:20s} → {info['label']}")
        print(f"   {INPUT_HOTKEY:20s} → Ask (Input Box)")
        print()
        keyboard.wait()

    def _on_input_hotkey(self):
        """Open input box for free-form prompts."""
        winsound.Beep(1200, 80)
        print("🔑 Input box triggered!")
        InputPopupService.show(callback=self._process_command)

    def _process_command(self, user_prompt: str):
        """Process the user's free-form command."""
        print(f"💬 Command: {user_prompt}")

        # Don't show big popup for agent commands — status bar handles it
        intent = self.command_service.detect_intent(user_prompt)
        if intent != "agent":
            PopupService.show("⏳ Processing...", title="Luffi · Ask")

        thread = threading.Thread(
            target=self._execute_command, args=(user_prompt,), daemon=True
        )
        thread.start()

    def _execute_command(self, user_prompt: str):
        """Execute command based on detected intent."""
        intent = self.command_service.detect_intent(user_prompt)
        context_text = None

        # AGENT MODE — desktop automation
        if intent == "agent":
            print(f"🤖 Agent mode: {user_prompt}")

            # No big popup during agent — uses small status bar instead
            result = self.agent_service.execute_command(user_prompt)
            winsound.Beep(2000, 100)
            # Show final result in big popup
            PopupService.show(result, title="Luffi · Agent · Done")
            return

        if intent == "screenshot":
            print("📸 Taking screenshot...")
            PopupService.show("📸 Capturing screen...", title="Luffi · Screenshot")
            context_text = self.command_service.capture_screenshot()
            if context_text and context_text.startswith("["):
                PopupService.show(context_text, title="Luffi · Error")
                return

        elif intent == "page_analysis":
            print("📄 Capturing page text...")
            PopupService.show("📄 Reading page...", title="Luffi · Page")
            context_text = self.command_service.capture_page_text()
            if not context_text:
                PopupService.show("⚠️ Could not capture page text", title="Luffi · Error")
                return

        # Build final prompt
        final_prompt = self.command_service.build_prompt(user_prompt, context_text)

        # Send to LLM
        try:
            response = httpx.post(
                f"http://{settings.host}:{settings.port}/explain",
                json={"text": final_prompt, "mode": "explain"},
                timeout=60.0,
            )
            if response.status_code == 200:
                data = response.json()
                explanation = data["explanation"]
                model = data["model_used"]
                latency = data.get("latency_ms", 0)
                tok_s = data.get("tokens_per_sec", 0)
                cached = data.get("from_cache", False)

                speed_tag = "⚡CACHED" if cached else f"{latency:.0f}ms · {tok_s} tok/s"
                print(f"✅ [Ask] {speed_tag} ({model})\n")
                winsound.Beep(2000, 100)
                PopupService.show(
                    explanation,
                    title=f"Luffi · Ask · {model} · {speed_tag}",
                )
            else:
                PopupService.show(f"❌ API error: {response.status_code}")
        except Exception as e:
            PopupService.show(f"❌ Error: {e}")
            logger.error(f"Command execution failed: {e}")

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
        PopupService.show("⏳ Thinking...", title=f"Luffi · {label}")

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
                latency = data.get("latency_ms", 0)
                tok_s = data.get("tokens_per_sec", 0)
                cached = data.get("from_cache", False)

                speed_tag = "⚡CACHED" if cached else f"{latency:.0f}ms · {tok_s} tok/s"
                print(f"✅ [{label}] {speed_tag} ({model})\n")
                winsound.Beep(2000, 100)
                PopupService.show(
                    explanation,
                    title=f"Luffi · {label} · {model} · {speed_tag}",
                )
            else:
                winsound.Beep(400, 300)
                PopupService.show(f"❌ Error: API returned {response.status_code}")
        except Exception as e:
            winsound.Beep(400, 300)
            PopupService.show(f"❌ Error: {e}")
            logger.error(f"LLM call failed: {e}")
