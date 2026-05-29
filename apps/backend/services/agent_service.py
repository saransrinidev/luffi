"""
Agent Service — Thin wrapper around the layered agent orchestrator.
Keeps backward compatibility with existing routes and hotkey service.
"""
import logging
from agent.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class AgentService:
    """Delegates to the layered agent orchestrator."""

    def __init__(self):
        self.orchestrator = AgentOrchestrator()

    def execute_command(self, user_command: str, on_status=None) -> str:
        """Execute a command through the layered agent pipeline."""
        return self.orchestrator.run(user_command)
