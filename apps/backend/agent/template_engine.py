"""
Layer 2: Template Engine — Deterministic action sequences.
Skips LLM entirely for known task patterns.
If template matches with high confidence, execute directly.
"""
import logging
import re
from agent.intent_layer import Intent

logger = logging.getLogger(__name__)


class ActionStep:
    """Single execution step."""

    def __init__(self, action: str, **kwargs):
        self.action = action  # launch, click, type, key, wait, done
        self.params = kwargs

    def __str__(self):
        return f"{self.action}({self.params})"


class TemplateResult:
    """Result from template matching."""

    def __init__(self, steps: list[ActionStep], confidence: float):
        self.steps = steps
        self.confidence = confidence  # 0.0 to 1.0

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.8


# Template definitions
TEMPLATES = {
    "browser_search": lambda intent: TemplateResult(
        steps=[
            ActionStep("launch", app=_resolve_browser(intent.app)),
            ActionStep("wait", seconds=2),
            ActionStep("key", keys="ctrl+l"),
            ActionStep("wait", seconds=0.3),
            ActionStep("type", text=intent.goal),
            ActionStep("key", keys="enter"),
            ActionStep("wait", seconds=1),
            ActionStep("done", message=f"Searched '{intent.goal}'"),
        ],
        confidence=0.95,
    ),

    "browser_navigate": lambda intent: TemplateResult(
        steps=[
            ActionStep("launch", app=_resolve_browser(intent.app)),
            ActionStep("wait", seconds=2),
            ActionStep("key", keys="ctrl+l"),
            ActionStep("wait", seconds=0.3),
            ActionStep("type", text=intent.goal),
            ActionStep("key", keys="enter"),
            ActionStep("wait", seconds=1),
            ActionStep("done", message=f"Navigated to {intent.goal}"),
        ],
        confidence=0.95,
    ),

    "app_launch": lambda intent: TemplateResult(
        steps=[
            ActionStep("launch", app=intent.app),
            ActionStep("wait", seconds=2),
            ActionStep("done", message=f"Opened {intent.app}"),
        ],
        confidence=0.95,
    ),

    "calculator_compute": lambda intent: _build_calculator_steps(intent),

    "explorer_navigate": lambda intent: TemplateResult(
        steps=[
            ActionStep("launch", app="explorer"),
            ActionStep("wait", seconds=1),
            ActionStep("key", keys="ctrl+l"),
            ActionStep("wait", seconds=0.3),
            ActionStep("type", text=intent.goal),
            ActionStep("key", keys="enter"),
            ActionStep("done", message=f"Navigated to {intent.goal}"),
        ],
        confidence=0.9,
    ),

    "hotkey_action": lambda intent: TemplateResult(
        steps=[
            ActionStep("key", keys=intent.params.get("keys", "")),
            ActionStep("done", message=f"Pressed {intent.params.get('keys', '')}"),
        ],
        confidence=0.95,
    ),

    "type_text": lambda intent: TemplateResult(
        steps=[
            ActionStep("type", text=intent.goal),
            ActionStep("done", message=f"Typed '{intent.goal[:30]}'"),
        ],
        confidence=0.9,
    ),
}


def _resolve_browser(app: str) -> str:
    """Resolve browser name to executable."""
    browsers = {"browser": "firefox", "firefox": "firefox",
                "chrome": "chrome", "edge": "msedge"}
    return browsers.get(app.lower(), "firefox")


def _build_calculator_steps(intent: Intent) -> TemplateResult:
    """Build calculator steps — clicks buttons visually with cursor."""
    expr = intent.goal.strip()

    steps = [
        ActionStep("launch", app="calc"),
        ActionStep("wait", seconds=2),
    ]

    # Map characters to calculator button names + keyboard fallback
    # Windows Calculator UIAutomation names
    BUTTON_NAMES = {
        "0": ("Zero", "0"), "1": ("One", "1"), "2": ("Two", "2"),
        "3": ("Three", "3"), "4": ("Four", "4"), "5": ("Five", "5"),
        "6": ("Six", "6"), "7": ("Seven", "7"), "8": ("Eight", "8"),
        "9": ("Nine", "9"),
        "+": ("Plus", "+"), "-": ("Minus", "-"),
        "*": ("Multiply by", "*"), "/": ("Divide by", "/"),
        "=": ("Equals", "="), ".": ("Decimal", "."),
    }

    for char in expr:
        if char in BUTTON_NAMES:
            name, key = BUTTON_NAMES[char]
            steps.append(ActionStep("click_button", name=name, fallback_key=key))
            steps.append(ActionStep("wait", seconds=0.2))
        elif char == " ":
            continue

    # Press equals
    steps.append(ActionStep("click_button", name="Equals", fallback_key="="))
    steps.append(ActionStep("wait", seconds=0.5))
    steps.append(ActionStep("done", message=f"Calculated {expr}"))

    return TemplateResult(steps=steps, confidence=0.9)


class TemplateEngine:
    """Matches intents to deterministic action templates."""

    def match(self, intent: Intent) -> TemplateResult | None:
        """Try to find a template for the given intent."""
        builder = TEMPLATES.get(intent.action_type)
        if builder:
            result = builder(intent)
            logger.info(f"Template matched: {intent.action_type} (confidence={result.confidence})")
            return result

        logger.info(f"No template for: {intent.action_type}")
        return None
