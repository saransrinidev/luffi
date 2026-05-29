"""
Layer 5: Lightweight Decision Layer
3B model sees ONLY the goal + 3-5 candidates.
Returns ONLY an index number. Minimal reasoning required.
"""
import logging
import httpx
from config import get_settings
from agent.ui_layer import ScoredCandidate

logger = logging.getLogger(__name__)
settings = get_settings()


class DecisionLayer:
    """Asks LLM to pick from a tiny candidate list."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.slm_fast_model  # Even 1B can pick from 3-5 options

    def pick_element(self, goal: str, candidates: list[ScoredCandidate]) -> int | None:
        """
        Ask LLM to pick the best candidate index.
        Returns index (0-based) or None if failed.
        """
        if not candidates:
            return None

        # If only one candidate with high score, skip LLM
        if len(candidates) == 1:
            return 0

        if candidates[0].score >= 10 and candidates[0].score > candidates[1].score + 3:
            logger.info(f"Auto-pick (high confidence): {candidates[0]}")
            return 0

        # Build minimal prompt
        options = ""
        for i, c in enumerate(candidates):
            options += f"{i}: {c.element.control_type} \"{c.element.name}\"\n"

        prompt = f"""Pick the best option for: {goal}
{options}
Answer with ONLY the number:"""

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 5,
                        "num_ctx": 256,
                    },
                },
                timeout=15.0,
            )
            raw = resp.json().get("response", "").strip()
            logger.info(f"Decision LLM: '{raw}'")

            # Extract number
            for char in raw:
                if char.isdigit():
                    idx = int(char)
                    if 0 <= idx < len(candidates):
                        return idx

        except Exception as e:
            logger.error(f"Decision LLM failed: {e}")

        # Fallback: pick highest scored
        return 0
