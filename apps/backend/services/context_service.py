import logging

logger = logging.getLogger(__name__)

try:
    import win32gui
    import win32process
    import psutil
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False
    logger.warning("pywin32/psutil not installed — context detection disabled")


class ContextService:
    """Detects the active application for context-aware prompts."""

    # Map process names to context hints
    APP_CONTEXTS = {
        "code.exe": "vscode",
        "devenv.exe": "visual_studio",
        "chrome.exe": "browser",
        "msedge.exe": "browser",
        "firefox.exe": "browser",
        "WindowsTerminal.exe": "terminal",
        "cmd.exe": "terminal",
        "powershell.exe": "terminal",
        "notepad.exe": "text_editor",
        "WINWORD.EXE": "word",
        "EXCEL.EXE": "excel",
        "Discord.exe": "chat",
        "Telegram.exe": "chat",
    }

    @staticmethod
    def get_active_app() -> dict:
        """Get info about the currently focused application."""
        if not CONTEXT_AVAILABLE:
            return {"app": "unknown", "context": "general", "title": ""}

        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            exe_name = process.name()

            context = ContextService.APP_CONTEXTS.get(exe_name, "general")

            return {
                "app": exe_name,
                "context": context,
                "title": title,
            }
        except Exception as e:
            logger.error(f"Context detection failed: {e}")
            return {"app": "unknown", "context": "general", "title": ""}

    @staticmethod
    def get_context_hint(context: str) -> str:
        """Get additional prompt hint based on context."""
        hints = {
            "vscode": "The user is in a code editor. Assume the text is code or code-related.",
            "browser": "The user is in a web browser. The text might be from a webpage.",
            "terminal": "The user is in a terminal. The text is likely a command or output.",
            "text_editor": "The user is in a text editor.",
            "word": "The user is in Microsoft Word. The text is likely a document.",
            "excel": "The user is in Excel. The text might be formulas or data.",
            "chat": "The user is in a chat app. The text is a message.",
            "general": "",
        }
        return hints.get(context, "")
