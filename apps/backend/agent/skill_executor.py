"""
Skill Executor — Maps planner skills to real desktop actions.

Takes the atomic skills from the Planner Layer and executes them.
For "click" skills (which need a target on screen), it uses the
UI Layer + Decision Layer to find and click the right element.
"""
import logging
import time
import os
import pyautogui
from agent.planner_layer import PlannerStep
from agent.execution_layer import ExecutionLayer
from agent.ui_layer import UILayer
from agent.decision_layer import DecisionLayer
from services.mouse_service import human_click, human_type

logger = logging.getLogger(__name__)


class SkillResult:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message

    def __str__(self):
        return f"{'✓' if self.success else '✗'} {self.message}"


# Map location names to real paths
LOCATIONS = {
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
}


class SkillExecutor:
    """Executes atomic skills from the planner."""

    def __init__(self):
        self.exec_layer = ExecutionLayer()
        self.ui_layer = UILayer()
        self.decision_layer = DecisionLayer()

    def execute_skill(self, step: PlannerStep) -> SkillResult:
        """Route a skill to its handler."""
        skill = step.skill
        p = step.params

        try:
            if skill == "open_app":
                app = p.get("app") or p.get("app_name", "")
                result = self.exec_layer.execute_step(
                    self._mk("launch", app=app)
                )
                time.sleep(1.5)  # let app open
                return SkillResult(result.success, result.message)

            elif skill == "focus_window":
                return self._focus_window(p.get("window_name") or p.get("window", ""))

            elif skill == "type":
                text = p.get("text", "")
                time.sleep(0.3)
                human_type(text)
                return SkillResult(True, f"typed '{text[:30]}'")

            elif skill == "press":
                key = p.get("key", "")
                if "+" in key:
                    pyautogui.hotkey(*[k.strip() for k in key.split("+")])
                else:
                    pyautogui.press(key)
                return SkillResult(True, f"pressed {key}")

            elif skill == "click":
                return self._click_target(p.get("target", ""))

            elif skill == "save_file":
                return self._save_file(
                    p.get("location", "desktop"),
                    p.get("filename", "untitled"),
                )

            elif skill == "wait":
                cond = p.get("condition", "")
                time.sleep(1.5)
                return SkillResult(True, f"waited ({cond})")

            else:
                return SkillResult(False, f"unknown skill: {skill}")

        except Exception as e:
            logger.error(f"Skill execution error: {e}")
            return SkillResult(False, f"error: {e}")

    def _mk(self, action, **kwargs):
        """Create an ActionStep."""
        from agent.template_engine import ActionStep
        return ActionStep(action, **kwargs)

    def _focus_window(self, window_name: str) -> SkillResult:
        """Bring a window to foreground by partial title match."""
        import ctypes
        # Simple approach: alt+tab won't be reliable, so we just verify
        state = self.ui_layer.get_state()
        if window_name.lower() in state.foreground_app.lower():
            return SkillResult(True, f"already focused: {window_name}")
        # Could implement window enumeration here
        return SkillResult(True, f"focus attempted: {window_name}")

    def _click_target(self, target: str) -> SkillResult:
        """Find a target element on screen and click it."""
        # Get candidates matching the target description
        candidates = self.ui_layer.get_candidates(
            action_type="click_element",
            goal=target,
        )

        if not candidates:
            return SkillResult(False, f"target '{target}' not found on screen")

        # Let decision layer pick the best match
        idx = self.decision_layer.pick_element(target, candidates)
        if idx is None:
            idx = 0

        chosen = candidates[idx]
        human_click(chosen.element.x, chosen.element.y)
        return SkillResult(True, f"clicked '{chosen.element.name}'")

    def _save_file(self, location: str, filename: str) -> SkillResult:
        """Handle a save dialog: type path + filename, press enter."""
        time.sleep(0.5)
        folder = LOCATIONS.get(location.lower(), location)

        # Build full path
        if filename and not filename.endswith((".txt", ".png", ".docx")):
            filename += ".txt"
        full_path = os.path.join(folder, filename) if filename else folder

        # In a save dialog, type the full path and press enter
        human_type(full_path)
        time.sleep(0.3)
        pyautogui.press("enter")
        return SkillResult(True, f"saved to {full_path}")

    def execute_plan(self, steps: list[PlannerStep], on_step=None) -> list[SkillResult]:
        """Execute a full plan of skills."""
        results = []
        for i, step in enumerate(steps):
            if on_step:
                on_step(i, step)
            result = self.execute_skill(step)
            results.append(result)
            logger.info(f"  Skill {i+1}: {result}")

            # Human-like pause between skills
            time.sleep(0.6)

            if not result.success:
                break

        return results
