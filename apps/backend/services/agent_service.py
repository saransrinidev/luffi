"""
Luffi Agent — Local AI desktop automation with perception loop.

Architecture (same as Yuki, but local LLM):
1. Pre-launch app (reliable, no LLM needed)
2. Capture desktop state (UI tree + cursor + active window)
3. Send state + command to local Ollama
4. LLM returns next action (JSON)
5. Execute action (PyAutoGUI)
6. Recapture state → loop until done
"""
import logging
import time
import json
import ctypes
import pyautogui
import subprocess
import httpx
from config import get_settings
from services.desktop_service import DesktopService
from services.status_bar_service import StatusBarService
from services.mouse_service import human_click, human_move

logger = logging.getLogger(__name__)
settings = get_settings()

pyautogui.PAUSE = 0.15
pyautogui.FAILSAFE = True


class AgentService:
    """Full perception-loop agent using local LLM."""

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
        self.desktop = DesktopService()
        self.max_loops = 7
        self.history: list[str] = []

    def execute_command(self, user_command: str, on_status=None):
        """Main loop: pre-launch → see → think → act → repeat."""
        def status(msg):
            logger.info(msg)
            StatusBarService.show(msg)
            if on_status:
                on_status(msg)

        self.history = []
        status(f"🤖 {user_command}")

        # Step 0: Pre-launch any app mentioned in command
        self._pre_launch(user_command, status)

        # Main perception loop
        for loop in range(self.max_loops):
            # SEE
            status(f"👁️ Observing... (step {loop + 1})")
            state = self.desktop.refresh()
            print(f"   📺 Active: {state.foreground_app} | Elements: {len(state.elements)}")
            if loop == 0:
                for el in state.elements[:10]:
                    print(f"      {el}")

            # THINK
            status("🧠 Thinking...")
            action = self._ask_llm(user_command, state)

            if not action:
                status("❌ No valid action from LLM")
                StatusBarService.hide()
                return "Failed — LLM could not plan an action."

            act_type = action.get("action", "")
            desc = self._describe(action)

            # Block launch attempts (already handled by pre-launch)
            if act_type == "launch":
                self.history.append(f"BLOCKED launch (already open)")
                continue

            status(f"▶ {act_type} {desc}")

            # Detect repeat
            action_key = f"{act_type} {desc}"
            repeats = sum(1 for h in self.history[-4:] if action_key in h)
            if repeats >= 2:
                status("⚠️ Loop detected — stopping")
                StatusBarService.hide()
                log = "\n".join(f"  {h}" for h in self.history)
                return f"Stopped (loop detected).\n\nSteps:\n{log}"

            # ACT
            result = self._execute_action(action, state)
            self.history.append(f"{action_key} → {result}")

            # Done?
            if act_type == "done":
                msg = action.get("message", "Task complete")
                status(f"✅ {msg}")
                StatusBarService.hide()
                log = "\n".join(f"  {h}" for h in self.history)
                return f"{msg}\n\nSteps:\n{log}"

            time.sleep(0.5)

        StatusBarService.hide()
        log = "\n".join(f"  {h}" for h in self.history)
        return f"Max steps reached.\n\nSteps:\n{log}"

    def _pre_launch(self, command: str, status):
        """Pre-launch any app mentioned in the command."""
        lower = command.lower()
        for app_name, exe in self.APP_MAP.items():
            if app_name in lower:
                status(f"🚀 Launching {app_name}...")
                subprocess.Popen(f"start {exe}", shell=True)

                # Wait for it to become foreground
                for _ in range(10):
                    time.sleep(0.5)
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.lower()
                    if app_name in title or exe in title:
                        break

                time.sleep(1)
                self.desktop._cache = None
                self.history.append(f"launch → {app_name} → opened")
                status(f"✅ {app_name} opened")
                return

    def _ask_llm(self, command: str, state) -> dict | None:
        """Send current state to LLM, get one action back."""
        step_num = len(self.history) + 1

        done_summary = ""
        if self.history:
            done_summary = "Done: " + "; ".join(self.history[-3:]) + "\n"

        prompt = f"""Task: {command}
The app is already open. Interact with it.
{done_summary}
App: {state.foreground_app}
Elements:
{self._format_elements_short(state)}

Step {step_num}: Return ONE JSON action.
Click button: {{"action":"click","label":0}}
Type text: {{"action":"type","text":"youtube.com"}}
Press key: {{"action":"key","keys":"enter"}}
Finished: {{"action":"done","message":"completed"}}
JSON:"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 60,
                "num_ctx": 1024,
                "top_k": 5,
                "top_p": 0.3,
            },
        }

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=90.0,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "").strip()
            logger.info(f"LLM raw: {raw[:200]}")
            return self._parse_action(raw)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None

    def _format_elements_short(self, state) -> str:
        """Format elements in shortest possible way."""
        lines = []
        for el in state.elements:
            lines.append(f'[{el.label}] {el.control_type} "{el.name}"')
        return "\n".join(lines) if lines else "(no elements)"

    def _parse_action(self, raw: str) -> dict | None:
        """Parse a single JSON action from LLM response."""
        raw = raw.strip()
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict) and "action" in obj:
                return obj
            if isinstance(obj, list) and obj:
                return obj[0]
        except json.JSONDecodeError:
            pass

        start = raw.find("{")
        end = raw.find("}", start)
        if start != -1 and end != -1:
            try:
                obj = json.loads(raw[start:end + 1])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass

        logger.error(f"Parse failed: {raw[:150]}")
        return None

    def _execute_action(self, action: dict, state) -> str:
        """Execute one action using PyAutoGUI."""
        act_type = action.get("action", "")

        # Auto-fix: type with key combo → key action
        if act_type == "type":
            text = action.get("text", "")
            key_words = ["ctrl+", "alt+", "shift+", "enter", "tab", "escape"]
            if any(text.lower().startswith(k) or text.lower() == k for k in key_words):
                act_type = "key"
                action = {"action": "key", "keys": text}

        try:
            if act_type == "click":
                return self._do_click(action, state)

            elif act_type == "type":
                text = action.get("text", "")
                time.sleep(0.1)
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
                    pyautogui.hotkey(*[k.strip() for k in keys.split("+")])
                else:
                    pyautogui.press(keys)
                return f"pressed {keys}"

            elif act_type == "wait":
                secs = float(action.get("seconds", 1))
                time.sleep(secs)
                return f"waited {secs}s"

            elif act_type == "done":
                return action.get("message", "done")

            else:
                return f"unknown: {act_type}"

        except Exception as e:
            return f"error: {e}"

    def _do_click(self, action: dict, state) -> str:
        """Click element by label number with human-like movement."""
        label = action.get("label")
        if label is None:
            x, y = action.get("x"), action.get("y")
            if x and y:
                human_click(int(x), int(y))
                return f"clicked ({x}, {y})"
            return "no label or coordinates"

        label = int(label)
        for el in state.elements:
            if el.label == label:
                human_click(el.x, el.y)
                time.sleep(0.2)
                return f'clicked [{label}] "{el.name}" at ({el.x}, {el.y})'

        return f"element [{label}] not found"

    def _describe(self, action: dict) -> str:
        """Short description for logging."""
        act = action.get("action", "")
        if act == "click":
            return f"→ [{action.get('label', '?')}]"
        elif act == "type":
            return f"→ '{action.get('text', '')[:25]}'"
        elif act == "key":
            return f"→ {action.get('keys', '')}"
        elif act == "wait":
            return f"→ {action.get('seconds')}s"
        elif act == "done":
            return f"→ {action.get('message', '')[:30]}"
        return ""
