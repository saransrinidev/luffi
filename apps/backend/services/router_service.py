import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskComplexity:
    SIMPLE = "simple"      # Short text, single word, basic lookup
    MEDIUM = "medium"      # Paragraph, code snippet, normal question
    COMPLEX = "complex"    # Long text, multi-part, deep analysis


class RouterService:
    """
    SLM Smart Router — routes queries to the right model based on complexity.
    
    Strategy:
    - Simple tasks (< 50 chars, single words) → 1B model (instant)
    - Medium tasks (normal text/code) → 3B model (fast)
    - Complex tasks (long text, code review) → larger model (thorough)
    
    This avoids wasting a big model on "what does API mean?"
    """

    # Modes that always need deeper thinking
    COMPLEX_MODES = {"code_review"}
    SIMPLE_MODES = {"translate"}

    def __init__(self):
        self.fast_model = settings.slm_fast_model
        self.medium_model = settings.slm_medium_model
        self.heavy_model = settings.slm_heavy_model

    def classify(self, text: str, mode: str) -> str:
        """Classify task complexity."""
        # Mode-based override
        if mode in self.COMPLEX_MODES:
            return TaskComplexity.COMPLEX
        if mode in self.SIMPLE_MODES and len(text) < 100:
            return TaskComplexity.SIMPLE

        # Length-based heuristic
        word_count = len(text.split())

        if word_count <= 5:
            return TaskComplexity.SIMPLE
        elif word_count <= 80:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.COMPLEX

    def select_model(self, text: str, mode: str) -> str:
        """Select optimal model for the task."""
        complexity = self.classify(text, mode)

        if complexity == TaskComplexity.SIMPLE:
            model = self.fast_model
        elif complexity == TaskComplexity.COMPLEX:
            model = self.heavy_model
        else:
            model = self.medium_model

        logger.info(f"Router: [{complexity}] → {model}")
        return model

    def get_token_limit(self, text: str, mode: str) -> int:
        """Adjust max output tokens based on complexity."""
        complexity = self.classify(text, mode)

        if complexity == TaskComplexity.SIMPLE:
            return 80   # Short answer
        elif complexity == TaskComplexity.COMPLEX:
            return 300  # Detailed response
        else:
            return 150  # Normal response
