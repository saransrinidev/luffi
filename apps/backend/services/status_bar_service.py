"""
Status Bar — small rectangle at bottom-left of screen.
Shows agent progress without interfering with screen capture or UI elements.
"""
import threading
import logging
import tkinter as tk
from tkinter import font as tkfont
import queue

logger = logging.getLogger(__name__)

_status_queue = queue.Queue()
_bar_thread = None
_bar_ready = threading.Event()


class StatusBarService:
    """
    Tiny status bar at bottom-left corner (above taskbar).
    Non-intrusive — doesn't block UI automation or screen capture.
    """

    @staticmethod
    def show(text: str):
        """Update the status bar text."""
        global _bar_thread

        if _bar_thread is None or not _bar_thread.is_alive():
            _bar_ready.clear()
            _bar_thread = threading.Thread(target=StatusBarService._run, daemon=False)
            _bar_thread.start()
            _bar_ready.wait(timeout=3)

        _status_queue.put(text)

    @staticmethod
    def hide():
        """Hide the status bar."""
        _status_queue.put("__HIDE__")

    @staticmethod
    def _run():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.85)

        bg = "#0c0c0c"
        fg = "#16c60c"

        # Small bar: bottom-left, just above taskbar
        bar_width = 320
        bar_height = 28
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = 8
        y = screen_h - bar_height - 48  # above taskbar

        root.geometry(f"{bar_width}x{bar_height}+{x}+{y}")
        root.configure(bg=bg)

        # Border
        frame = tk.Frame(root, bg=bg, highlightbackground="#333333",
                         highlightthickness=1)
        frame.pack(fill="both", expand=True)

        # Status text
        status_font = tkfont.Font(family="Consolas", size=8)
        label = tk.Label(frame, text="⚡ Luffi Agent", font=status_font,
                         fg=fg, bg=bg, anchor="w", padx=6)
        label.pack(fill="both", expand=True)

        root.withdraw()  # Start hidden

        _bar_ready.set()

        def check_queue():
            try:
                while True:
                    msg = _status_queue.get_nowait()

                    if msg == "__HIDE__":
                        root.withdraw()
                    else:
                        # Truncate long messages
                        display = msg if len(msg) <= 45 else msg[:42] + "..."
                        label.config(text=f"⚡ {display}")
                        root.deiconify()
                        root.lift()
            except queue.Empty:
                pass

            root.after(100, check_queue)

        check_queue()
        root.mainloop()
