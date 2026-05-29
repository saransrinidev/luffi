import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationService:
    """Maintains conversation context for follow-up questions."""

    def __init__(self, timeout_minutes: int = 5):
        self.messages: list[dict] = []
        self.last_interaction: datetime | None = None
        self.timeout = timedelta(minutes=timeout_minutes)

    def add_user_message(self, text: str):
        """Add user input to conversation."""
        self._check_timeout()
        self.messages.append({"role": "user", "content": text})
        self.last_interaction = datetime.now()

    def add_assistant_message(self, text: str):
        """Add assistant response to conversation."""
        self.messages.append({"role": "assistant", "content": text})
        self.last_interaction = datetime.now()

    def get_context_prompt(self, new_text: str) -> str:
        """Build prompt with conversation history."""
        self._check_timeout()

        if not self.messages:
            return new_text

        context = "Previous conversation:\n"
        # Keep last 6 messages for context
        recent = self.messages[-6:]
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content'][:200]}\n"

        context += f"\nNew question/text: {new_text}"
        return context

    def clear(self):
        """Clear conversation history."""
        self.messages = []
        self.last_interaction = None
        logger.info("Conversation cleared")

    def _check_timeout(self):
        """Auto-clear if conversation timed out."""
        if self.last_interaction and datetime.now() - self.last_interaction > self.timeout:
            logger.info("Conversation timed out, clearing")
            self.clear()

    @property
    def has_context(self) -> bool:
        return len(self.messages) > 0
