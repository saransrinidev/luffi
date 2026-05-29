import logging
import pyperclip
import pyautogui
import time
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class CommandService:
    """
    Processes free-form user commands.
    
    Detects intent from the prompt and routes to:
    - screenshot → captures screen, OCR, sends to LLM
    - page analysis → grabs visible text, sends to LLM
    - automation → launches agent to control desktop
    - anything else → sends as direct prompt to LLM
    """

    # Keywords that trigger screenshot
    SCREENSHOT_KEYWORDS = ["screenshot", "capture screen", "what's on screen", "whats on screen"]

    # Keywords that trigger page analysis
    PAGE_KEYWORDS = ["analyse page", "analyze page", "summarize page", "page summary",
                     "this page", "current page", "what's on this page"]

    # Keywords that trigger desktop automation agent
    AGENT_KEYWORDS = [
        "open ", "launch ", "close ", "click ", "go to ", "navigate to ",
        "search for ", "type ", "switch to ", "minimize", "maximize",
        "new tab", "open browser", "open firefox", "open chrome",
        "open notepad", "open terminal", "open cmd", "open explorer",
        "play ", "pause", "next tab", "close tab",
    ]

    @staticmethod
    def detect_intent(prompt: str) -> str:
        """Detect what the user wants to do."""
        lower = prompt.lower().strip()

        # Check agent keywords first (automation commands)
        for kw in CommandService.AGENT_KEYWORDS:
            if lower.startswith(kw) or kw in lower:
                return "agent"

        for kw in CommandService.SCREENSHOT_KEYWORDS:
            if kw in lower:
                return "screenshot"

        for kw in CommandService.PAGE_KEYWORDS:
            if kw in lower:
                return "page_analysis"

        return "direct_prompt"

    @staticmethod
    def capture_screenshot() -> str | None:
        """Take a screenshot and extract text via OCR."""
        try:
            from PIL import ImageGrab
        except ImportError:
            return "[Error: Pillow not installed]"

        try:
            img = ImageGrab.grab()
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(tmp.name)

            try:
                import easyocr
                reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                results = reader.readtext(tmp.name)
                text = "\n".join([r[1] for r in results])
                Path(tmp.name).unlink(missing_ok=True)
                return text.strip() if text.strip() else "[No text detected on screen]"
            except ImportError:
                Path(tmp.name).unlink(missing_ok=True)
                return "[OCR not available — install easyocr: pip install easyocr]"

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return f"[Screenshot error: {e}]"

    @staticmethod
    def capture_page_text() -> str | None:
        """Try to grab all text from current page via Ctrl+A, Ctrl+C."""
        try:
            old_clipboard = pyperclip.paste()

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.15)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.15)

            text = pyperclip.paste()
            pyautogui.press("right")

            if not text or text == old_clipboard:
                pyperclip.copy(old_clipboard)
                return None

            return text.strip()

        except Exception as e:
            logger.error(f"Page capture failed: {e}")
            return None

    @staticmethod
    def build_prompt(user_prompt: str, context_text: str | None) -> str:
        """Build the final prompt to send to LLM."""
        if context_text:
            return f"{user_prompt}\n\nContent:\n{context_text}"
        return user_prompt
