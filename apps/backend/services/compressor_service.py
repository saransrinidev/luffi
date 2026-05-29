import re
import logging

logger = logging.getLogger(__name__)


class CompressorService:
    """
    Prompt Compressor — reduces input size for faster inference.
    
    SLM models are faster with shorter inputs. This service:
    1. Strips unnecessary whitespace
    2. Removes comments from code
    3. Truncates overly long inputs
    4. Compresses repeated patterns
    
    Less tokens in = faster generation.
    """

    MAX_INPUT_CHARS = 800  # Hard limit on input text

    @staticmethod
    def compress(text: str) -> str:
        """Compress text for faster LLM processing."""
        original_len = len(text)

        # Strip excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{4,}", "  ", text)

        # Remove common code comments (single-line)
        text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*#(?!!).*$", "", text, flags=re.MULTILINE)

        # Remove empty lines left after comment removal
        text = re.sub(r"\n{2,}", "\n", text)

        # Truncate if still too long
        if len(text) > CompressorService.MAX_INPUT_CHARS:
            text = text[: CompressorService.MAX_INPUT_CHARS] + "\n...[truncated]"

        text = text.strip()
        compressed_len = len(text)

        if original_len != compressed_len:
            ratio = (1 - compressed_len / original_len) * 100
            logger.info(f"Compressed: {original_len} → {compressed_len} chars ({ratio:.0f}% reduction)")

        return text

    @staticmethod
    def compress_prompt(prompt: str) -> str:
        """Compress the system prompt itself for fewer tokens."""
        # Remove extra instruction fluff — keep it tight
        prompt = re.sub(r"\s+", " ", prompt)
        return prompt.strip()
