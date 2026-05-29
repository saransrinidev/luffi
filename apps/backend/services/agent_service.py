import logging
import time
import json
import pyautogui
import httpx
import subprocess
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

pyautogui.PAUSE = 0.3
pyautogui.FAILSAFE = True


# Keep prompt VERY short — 3B models need minimal instructions
AGENT_PROMPT = """Return a JSON array of actions to do this task on Windows.
Actions: launch, click, type, key, wait, done.
Format: [{"action":"launch","app":"firefox"},{"action":"wait","seconds":2},{"action":"key","keys":"ctrl+l"},{"action":"type","text":"youtube.com"},{"action":"key","keys":"enter"},{"action":"done","message":"opened youtube"}]
Only return JSON array, nothing else.

Task: """


class AgentService:
    """Local AI Agent — plans and executes desktop automation."""

    APP_MAP = {
        "firefox": "firefox",
        "chrome": "chrome",
        "notepad": "notepad",
        "explorer": "explorer",
        "cmd": "cmd",
        "terminal": "wt",
        "code": "code",
        "vscode": "code",
        "edge": "msedge",
        "calculator": "calc",
        "paint": "mspaint",
    }

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.slm_medium_model

    def execute_command(self, user_command: str, on_status=None):
        """Plan and execute a desktop command."""
        def status(msg):
            logger.info(msg)
            if on_status:
                on_status(msg)

        status(f"🤖 Planning: {user_command}")

        actions = self._get_actions(user_command)

        if not actions:
            # Fallback: try simple direct execution for common commands
            fallback = self._try_fallback(user_command)
            if fallback:
                status(f"⚡ Fallback: {fallback}")
                return fallback
            status("❌ Could not plan actions")
            return "Failed to plan actions."

        status(f"📋 Executing {len(actions)} steps")

        results = []
        for i, action in enumerate(actions):
            act_type = action.get("action", "")
            desc = self._describe(action)
            status(f"  [{i+1}] {act_type} {desc}")

            result = self._execute_action(action)
            results.append(f"[{i+1}] {act_type}: {result}")

            if act_type == "done":
                break

        final_msg = "Done"
        for a in reversed(actions):
            if a.get("action") == "done":
                final_msg = a.get("message", "Done")
                break

        status(f"✅ {final_msg}")
        return f"{final_msg}\n\n" + "\n".join(results)

    def _get_actions(self, command: str) -> list[dict] | None:
        """Ask LLM to plan actions. Minimal prompt for speed."""
        prompt = AGENT_PROMPT + command

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 300,
                "num_ctx": 1024,
                "top_k": 5,
                "top_p": 0.3,
                "stop": ["\n\n", "```"],
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=90.0,
            )
            response.raise_for_status()
            data = response.json()
            raw = data.get("response", "")
            logger.info(f"LLM response: {raw[:300]}")
            return self._parse_actions(raw)

        except httpx.TimeoutException:
            logger.error("LLM timed out (90s)")
            return None
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            return None

    def _try_fallback(self, command: str) -> str | None:
        """Handle common commands without LLM (instant)."""
        lower = command.lower().strip()

        # Direct app launch
        for app_name, exe in self.APP_MAP.items():
            if f"open {app_name}" in lower or f"launch {app_name}" in lower:
                subprocess.Popen(f"start {exe}", shell=True)
                time.sleep(1)

                # If "and go to" or "and search" is in command, handle URL
                if "go to " in lower or "search " in lower:
                    time.sleep(2)
                    # Focus address bar
                    pyautogui.hotkey("ctrl", "l")
                    time.sleep(0.3)

                    # Extract URL/search term
                    if "go to " in lower:
                        target = lower.split("go to ")[-1].strip()
                    elif "search " in lower:
                        target = lower.split("search ")[-1].strip()
                    else:
                        target = ""

                    if target:
                        pyautogui.typewrite(target, interval=0.02)
                        time.sleep(0.2)
                        pyautogui.press("enter")

                    return f"Opened {app_name} → {target}"

                return f"Opened {app_name}"

        # Simple key commands
        if "new tab" in lower:
            pyautogui.hotkey("ctrl", "t")
            return "Opened new tab"
        if "close tab" in lower:
            pyautogui.hotkey("ctrl", "w")
            return "Closed tab"
        if "minimize" in lower:
            pyautogui.hotkey("win", "down")
            return "Minimized"
        if "maximize" in lower:
            pyautogui.hotkey("win", "up")
            return "Maximized"

        return None

    def _parse_actions(self, raw: str) -> list[dict] | None:
        """Extract JSON array from LLM response."""
        raw = raw.strip()

        try:
            actions = json.loads(raw)
            if isinstance(actions, list):
                return actions
        except json.JSONDecodeError:
            pass

        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            try:
                actions = json.loads(raw[start:end + 1])
                if isinstance(actions, list):
                    return actions
            except json.JSONDecodeError:
                pass

        logger.error(f"Parse failed: {raw[:200]}")
        return None

    def _execute_action(self, action: dict) -> str:
        """Execute a single action."""
        act_type = action.get("action", "")

        try:
            if act_type == "launch":
                return self._launch(action.get("app", ""))
            elif act_type == "click":
                x, y = int(action.get("x", 0)), int(action.get("y", 0))
                pyautogui.click(x, y)
                return f"clicked ({x}, {y})"
            elif act_type == "type":
                text = action.get("text", "")
                if not text.isascii():
                    import pyperclip
                    pyperclip.copy(text)
                    pyautogui.hotkey("ctrl", "v")
                else:
                    pyautogui.typewrite(text, interval=0.02)
                return f"typed '{text[:30]}'"
            elif act_type == "key":
                keys = action.get("keys", "")
                if "+" in keys:
                    pyautogui.hotkey(*keys.split("+"))
                else:
                    pyautogui.press(keys)
                return f"pressed {keys}"
            elif act_type == "wait":
                seconds = float(action.get("seconds", 1))
                time.sleep(seconds)
                return f"waited {seconds}s"
            elif act_type == "scroll":
                direction = action.get("direction", "down")
                amount = int(action.get("amount", 3))
                pyautogui.scroll(amount if direction == "up" else -amount)
                return f"scrolled {direction}"
            elif act_type == "done":
                return action.get("message", "done")
            else:
                return f"unknown: {act_type}"
        except Exception as e:
            return f"error: {e}"

    def _launch(self, app: str) -> str:
        app_lower = app.lower().strip()
        exe = self.APP_MAP.get(app_lower, app_lower)
        try:
            subprocess.Popen(f"start {exe}", shell=True)
            time.sleep(0.5)
            return f"launched {exe}"
        except Exception as e:
            return f"failed: {e}"

    def _describe(self, action: dict) -> str:
        act = action.get("action", "")
        if act == "launch": return f"→ {action.get('app', '')}"
        elif act == "click": return f"→ ({action.get('x')}, {action.get('y')})"
        elif act == "type": return f"→ '{action.get('text', '')[:20]}'"
        elif act == "key": return f"→ {action.get('keys', '')}"
        elif act == "wait": return f"→ {action.get('seconds')}s"
        elif act == "done": return f"→ {action.get('message', '')[:30]}"
        return ""
