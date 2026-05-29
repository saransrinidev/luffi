import logging
import winsound

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

AVAILABLE_MODELS = [
    "llama3.2:3b",
    "phi4-mini",
    "gemma3",
]


class ModelService:
    """Manages model switching."""

    def __init__(self):
        self.models = AVAILABLE_MODELS
        self.current_index = 0
        # Set initial to config value
        if settings.ollama_model in self.models:
            self.current_index = self.models.index(settings.ollama_model)

    @property
    def current_model(self) -> str:
        return self.models[self.current_index]

    def cycle_next(self) -> str:
        """Switch to next model in list."""
        self.current_index = (self.current_index + 1) % len(self.models)
        model = self.current_model
        logger.info(f"Switched to model: {model}")
        winsound.Beep(1200, 100)
        winsound.Beep(1600, 100)
        print(f"🔄 Model switched to: {model}")
        return model

    def get_all(self) -> list[str]:
        return self.models
