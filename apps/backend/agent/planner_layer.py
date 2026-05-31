"""
Planner Layer — Breaks compound user requests into atomic skill calls.

The LLM acts ONLY as a planner, not an executor. It outputs a JSON array
of skills. This keeps the model's job simple: decompose, don't reason about
pixels or coordinates.

Skills:
  open_app(app_name)
  focus_window(window_name)
  type(text)
  press(key)
  click(target)
  save_file(location, filename)
  wait(condition)
"""
import json
import logging
import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


PLANNER_PROMPT = """You are Loopi, a desktop automation planner.
Your job is ONLY to convert user commands into action plans.

Available skills:
open_app(app)
type(text)
press(key)
click(target)
focus_window(name)
save_file(location, filename)
wait(condition)

STRICT RULES:
1. Split compound commands into multiple actions.
2. Never combine actions into one search query.
3. Output ONLY VALID JSON ARRAY.
4. JSON MUST start with [
5. JSON MUST end with ]
6. No markdown.
7. No explanations.
8. No extra text.
9. Use only available skills.
10. One action per object.

EXAMPLES
User: Open firefox and search youtube
[{"skill":"open_app","app":"firefox"},{"skill":"type","text":"youtube"},{"skill":"press","key":"enter"}]

User: Open firefox and search cat videos and click first result
[{"skill":"open_app","app":"firefox"},{"skill":"type","text":"cat videos"},{"skill":"press","key":"enter"},{"skill":"click","target":"first result"}]

User: Open notepad and write hello world
[{"skill":"open_app","app":"notepad"},{"skill":"type","text":"hello world"}]

User: Open notepad and write a poem and save to desktop
[{"skill":"open_app","app":"notepad"},{"skill":"type","text":"a poem"},{"skill":"press","key":"ctrl+s"},{"skill":"save_file","location":"desktop"}]

User: Open chrome and search memes and click images tab
[{"skill":"open_app","app":"chrome"},{"skill":"type","text":"memes"},{"skill":"press","key":"enter"},{"skill":"click","target":"images tab"}]

Now convert this user request into VALID JSON ARRAY ONLY.
User: """


class PlannerStep:
    """One planned skill call."""

    def __init__(self, skill: str, params: dict):
        self.skill = skill
        self.params = params

    def __str__(self):
        p = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.skill}({p})"


class PlannerLayer:
    """Uses LLM to decompose requests into skill sequences."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        # Use medium model (already installed). Switch to slm_agent_model
        # if you pull qwen2.5:7b for better planning quality.
        self.model = settings.slm_medium_model

    def plan(self, command: str) -> list[PlannerStep]:
        """Break a command into atomic skill steps."""
        prompt = PLANNER_PROMPT + command + "\n"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 300,
                "num_ctx": 1024,
                "top_k": 10,
                "top_p": 0.5,
                "stop": ["\nUser:", "```", "\n\n"],
            },
        }

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "").strip()
            logger.info(f"Planner raw: {raw[:300]}")
            return self._parse_plan(raw)

        except Exception as e:
            logger.error(f"Planner failed: {e}")
            return []

    def _parse_plan(self, raw: str) -> list[PlannerStep]:
        """Extract the JSON array of skills from LLM output.
        Resilient to missing brackets and extra text."""
        raw = raw.strip()

        # Remove markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()

        # Strip a leading "Output:" label if the model added one
        if raw.lower().startswith("output:"):
            raw = raw[7:].strip()

        arr = None

        # Attempt 1: direct array parse
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                arr = json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                arr = None

        # Attempt 2: missing brackets — reconstruct from {...} objects
        if arr is None:
            # Find all top-level {...} objects
            objects = self._extract_objects(raw)
            if objects:
                try:
                    arr = json.loads("[" + ",".join(objects) + "]")
                except json.JSONDecodeError:
                    arr = None

        if not arr:
            logger.error(f"Could not parse plan: {raw[:200]}")
            return []

        steps = []
        for item in arr:
            if not isinstance(item, dict) or "skill" not in item:
                continue
            skill = item.pop("skill")
            steps.append(PlannerStep(skill, item))

        return steps

    def _extract_objects(self, text: str) -> list[str]:
        """Extract individual {...} JSON objects from text using brace matching."""
        objects = []
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start != -1:
                    objects.append(text[start:i + 1])
                    start = -1
        return objects
