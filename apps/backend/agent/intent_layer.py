"""
Layer 1: Intent Extraction
Extracts structured intent from natural language.
Minimizes LLM reasoning — just classification + extraction.
"""
import re
import logging
import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Intent:
    """Structured intent extracted from user command."""

    def __init__(self, app: str, goal: str, action_type: str, params: dict = None):
        self.app = app
        self.goal = goal
        self.action_type = action_type
        self.params = params or {}

    def __str__(self):
        return f"Intent(app={self.app}, goal={self.goal}, type={self.action_type})"


# Regex-based intent patterns (no LLM needed for common cases)
PATTERNS = [
    # Browser
    (r"(?:open|launch)\s+(firefox|chrome|edge|browser)\s+(?:and\s+)?(?:search|go to|navigate to)\s+(.+)",
     lambda m: Intent(m.group(1), m.group(2).strip(), "browser_search")),

    (r"(?:search|google)\s+(.+)",
     lambda m: Intent("browser", m.group(1).strip(), "browser_search")),

    (r"(?:go to|open|visit)\s+(https?://\S+|[\w]+\.[\w]+\S*)",
     lambda m: Intent("browser", m.group(1).strip(), "browser_navigate")),

    # Calculator
    (r"(?:open\s+)?calculator?\s+(?:and\s+)?(?:calculate|compute|do)\s+(.+)",
     lambda m: Intent("calculator", m.group(1).strip(), "calculator_compute")),

    (r"(?:calculate|compute)\s+(.+)",
     lambda m: Intent("calculator", m.group(1).strip(), "calculator_compute")),

    # App launch
    (r"(?:open|launch|start)\s+(firefox|chrome|edge|notepad|calculator|explorer|cmd|terminal|code|vscode|paint)",
     lambda m: Intent(m.group(1).strip(), "open", "app_launch")),

    # File explorer
    (r"(?:open|go to|navigate to)\s+(?:folder|directory)\s+(.+)",
     lambda m: Intent("explorer", m.group(1).strip(), "explorer_navigate")),

    # Tab management
    (r"(?:new tab|open tab)",
     lambda m: Intent("browser", "new tab", "hotkey_action", {"keys": "ctrl+t"})),

    (r"(?:close tab)",
     lambda m: Intent("browser", "close tab", "hotkey_action", {"keys": "ctrl+w"})),

    # Typing
    (r"type\s+(.+)",
     lambda m: Intent("active", m.group(1).strip(), "type_text")),
]


class IntentLayer:
    """Extracts structured intent from user command."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.slm_fast_model  # 1B is enough for classification

    def extract(self, command: str) -> Intent:
        """Extract intent — tries regex first, falls back to LLM."""
        # Try regex patterns first (instant, no LLM)
        intent = self._regex_extract(command)
        if intent:
            logger.info(f"Intent (regex): {intent}")
            return intent

        # Fallback to LLM for unknown patterns
        intent = self._llm_extract(command)
        if intent:
            logger.info(f"Intent (LLM): {intent}")
            return intent

        # Last resort — generic
        return Intent("unknown", command, "generic")

    def _regex_extract(self, command: str) -> Intent | None:
        """Try to match command against known patterns."""
        lower = command.lower().strip()
        for pattern, builder in PATTERNS:
            match = re.match(pattern, lower)
            if match:
                return builder(match)
        return None

    def _llm_extract(self, command: str) -> Intent | None:
        """Use LLM for intent extraction (minimal prompt)."""
        prompt = f"""Classify this command. Return ONLY: app|goal|action_type
action_types: browser_search, browser_navigate, app_launch, calculator_compute, type_text, hotkey_action, click_element, generic

Command: {command}
Answer (format: app|goal|action_type):"""

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 30},
                },
                timeout=15.0,
            )
            raw = resp.json().get("response", "").strip()
            parts = raw.split("|")
            if len(parts) >= 3:
                return Intent(
                    app=parts[0].strip(),
                    goal=parts[1].strip(),
                    action_type=parts[2].strip(),
                )
        except Exception as e:
            logger.error(f"LLM intent extraction failed: {e}")

        return None
