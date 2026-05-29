import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPTS_FILE = Path(__file__).parent.parent / "prompts.json"


class PromptService:
    """Manages prompt templates for different modes."""

    def __init__(self):
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> dict:
        try:
            with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            return {}

    def reload(self):
        """Reload prompts from file (hot reload)."""
        self.prompts = self._load_prompts()
        logger.info(f"Reloaded {len(self.prompts)} prompts")

    def get_prompt(self, mode: str, text: str) -> str:
        """Get formatted prompt for a given mode."""
        if mode not in self.prompts:
            mode = "explain"
        template = self.prompts[mode]["prompt"]
        return template.replace("{text}", text)

    def get_modes(self) -> dict:
        """Return all available modes with their hotkeys."""
        return {
            key: {"hotkey": val["hotkey"], "label": val["label"]}
            for key, val in self.prompts.items()
        }

    def get_mode_by_hotkey(self, hotkey: str) -> str | None:
        """Find mode name by its hotkey."""
        for mode, config in self.prompts.items():
            if config["hotkey"] == hotkey:
                return mode
        return None
