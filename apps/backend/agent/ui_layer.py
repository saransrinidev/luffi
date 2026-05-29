"""
Layer 3: UI Retrieval — Collects UIAutomation tree.
Layer 4: Candidate Filtering — Scores and ranks elements.

NEVER sends full UI tree to LLM.
Returns only top 3-5 candidates based on heuristic scoring.
"""
import logging
from services.desktop_service import DesktopService, UIElement

logger = logging.getLogger(__name__)


# Semantic aliases — different names for same concept
ALIASES = {
    "address_bar": [
        "search or enter address", "address and search bar",
        "url", "address bar", "search bar", "omnibox",
        "search or type url", "enter address", "browser input",
    ],
    "search_field": [
        "search", "search box", "search field", "find",
        "search the web", "search google",
    ],
    "close_button": [
        "close", "x", "close window", "close tab",
    ],
    "back_button": [
        "back", "go back", "navigate back",
    ],
    "submit_button": [
        "submit", "go", "enter", "ok", "send", "search",
    ],
}


# Control type expectations per action type
EXPECTED_CONTROLS = {
    "browser_search": ["Edit"],
    "browser_navigate": ["Edit"],
    "type_text": ["Edit", "ComboBox"],
    "click_element": ["Button", "Link", "MenuItem", "TabItem"],
    "menu_navigation": ["MenuItem", "TabItem"],
    "button_action": ["Button"],
}


class ScoredCandidate:
    """UI element with relevance score."""

    def __init__(self, element: UIElement, score: float, reasons: list[str]):
        self.element = element
        self.score = score
        self.reasons = reasons

    def __str__(self):
        return (f"[{self.element.label}] {self.element.control_type} "
                f"\"{self.element.name}\" (score={self.score:.1f})")


class UILayer:
    """Retrieves UI state and filters candidates."""

    def __init__(self):
        self.desktop = DesktopService()

    def get_candidates(self, action_type: str, goal: str,
                       max_candidates: int = 5) -> list[ScoredCandidate]:
        """
        Get top candidates for the given action type and goal.
        Uses heuristic scoring — NO LLM involved.
        """
        state = self.desktop.refresh()

        if not state.elements:
            logger.warning("No UI elements found")
            return []

        # Score each element
        scored = []
        for el in state.elements:
            score, reasons = self._score_element(el, action_type, goal)
            if score > 0:
                scored.append(ScoredCandidate(el, score, reasons))

        # Sort by score descending
        scored.sort(key=lambda c: c.score, reverse=True)

        # Return top N
        top = scored[:max_candidates]

        for c in top:
            logger.info(f"  Candidate: {c}")

        return top

    def _score_element(self, el: UIElement, action_type: str, goal: str) -> tuple[float, list[str]]:
        """Score an element's relevance. Returns (score, reasons)."""
        score = 0.0
        reasons = []
        el_name_lower = el.name.lower()
        goal_lower = goal.lower()

        # 1. Control type match (+5)
        expected = EXPECTED_CONTROLS.get(action_type, [])
        if expected and el.control_type in expected:
            score += 5
            reasons.append(f"type_match:{el.control_type}")

        # 2. Name keyword match (+5)
        goal_words = goal_lower.split()
        for word in goal_words:
            if len(word) > 2 and word in el_name_lower:
                score += 5
                reasons.append(f"keyword:{word}")
                break

        # 3. Semantic alias match (+5)
        for concept, aliases in ALIASES.items():
            # Check if goal relates to this concept
            if any(a in goal_lower for a in aliases):
                # Check if element name matches any alias
                if any(a in el_name_lower for a in aliases):
                    score += 5
                    reasons.append(f"alias:{concept}")
                    break

        # 4. Action-type specific heuristics
        if action_type in ("browser_search", "browser_navigate"):
            # Address bar is usually an Edit with "address" or "search" in name
            if el.control_type == "Edit":
                if any(kw in el_name_lower for kw in ["address", "url", "search", "enter"]):
                    score += 8
                    reasons.append("address_bar_match")

        elif action_type == "calculator_compute":
            # Calculator buttons match digits/operators
            if el.control_type == "Button":
                if el.name in "0123456789+-*/=.":
                    score += 3
                    reasons.append("calc_button")
                if any(w in el_name_lower for w in goal_lower.split()):
                    score += 5
                    reasons.append("calc_match")

        # 5. Penalize unlikely elements
        if el.control_type in ("MenuItem",) and action_type in ("browser_search", "type_text"):
            score -= 3
            reasons.append("penalty:wrong_type")

        if "close" in el_name_lower and "close" not in goal_lower:
            score -= 2
            reasons.append("penalty:close_button")

        return score, reasons

    def get_state(self):
        """Get raw desktop state."""
        return self.desktop.refresh()
