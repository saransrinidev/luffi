import httpx
import logging

from config import get_settings
from services.prompt_service import PromptService

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.default_model = settings.ollama_model
        self.prompt_service = PromptService()

    async def explain(self, text: str, model: str | None = None, mode: str = "explain") -> dict:
        """Send text to Ollama with mode-specific prompt."""
        model_to_use = model or self.default_model
        prompt = self.prompt_service.get_prompt(mode, text)

        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
        }

        logger.info(f"[{mode}] Sending to Ollama ({model_to_use}): {text[:50]}...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        explanation = data.get("response", "No response from model.")
        logger.info(f"Received response ({len(explanation)} chars)")

        return {
            "explanation": explanation,
            "model_used": model_to_use,
            "mode": mode,
        }
