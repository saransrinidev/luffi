"""
Status Bar — small monochrome progress indicator at bottom-left.
Non-intrusive during agent runs.
"""
import threading
import logging
import tkinter as tk
from tkinter import font as tkfont
import queue

from services import theme as T
from services.theme import Icon

logger = logging.getLogger(__name__)

_status_queue = queue.Queue()
_bar_thread = None
_bar_ready = threading.Event()


class StatusBarService:
    """Tiny monochrome status bar, bottom-left above taskbar."""

    @staticmethod
    def show(text: str):
        global _bar_thread
        if _bar_thread is None or not _bar_thread.is_alive():
            _bar_ready.clear()
            _bar_thread = threading.Thread(target=StatusBarService._run, daemon=False)
            _bar_thread.start()
            _bar_ready.wait(timeout=3)
        _status_queue.put(text)

    @staticmethod
    def hide():
        _status_queue.put("__HIDE__")

    @staticmethod
    def _run():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.94)

        bar_width, bar_height = 340, 30
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = 12
        y = sh - bar_height - 52
        root.geometry(f"{bar_width}x{bar_height}+{x}+{y}")
        root.configure(bg=T.BG)

        frame = tk.Frame(root, bg=T.PANEL, highlightbackground=T.BORDER,
                         highlightthickness=1)
        frame.pack(fill="both", expand=True)

        logo_font = tkfont.Font(family=T.FONT_MAIN, size=9, weight="bold")
        tk.Label(frame, text=Icon.LOGO, font=logo_font,
                 fg=T.WHITE, bg=T.PANEL, padx=8).pack(side="left", fill="y")

        status_font = tkfont.Font(family=T.FONT_MAIN, size=9)
        label = tk.Label(frame, text="Luffi", font=status_font,
                         fg=T.TEXT, bg=T.PANEL, anchor="w")
        label.pack(side="left", fill="both", expand=True)

        root.withdraw()
        _bar_ready.set()

        def check_queue():
            try:
                while True:
                    msg = _status_queue.get_nowait()
                    if msg == "__HIDE__":
                        root.withdraw()
                    else:
                        display = msg if len(msg) <= 46 else msg[:43] + "..."
                        label.config(text=display)
                        root.deiconify()
                        root.lift()
            except queue.Empty:
                pass
            root.after(100, check_queue)

        check_queue()
        root.mainloop()
