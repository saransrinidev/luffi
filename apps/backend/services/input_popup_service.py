"""
Input Box — professional monochrome command bar.
Opens on hotkey, user types, presses Enter.
"""
import threading
import logging
import tkinter as tk
from tkinter import font as tkfont

from services import theme as T
from services.theme import Icon

logger = logging.getLogger(__name__)

_result_callback = None


class InputPopupService:
    """Monochrome command input bar."""

    @staticmethod
    def show(callback):
        global _result_callback
        _result_callback = callback
        thread = threading.Thread(target=InputPopupService._create_input, daemon=False)
        thread.start()

    @staticmethod
    def _create_input():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", T.ALPHA)

        width, height = 620, 110
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 3
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.configure(bg=T.BG)

        outer = tk.Frame(root, bg=T.BG, highlightbackground=T.BORDER,
                         highlightthickness=1)
        outer.pack(fill="both", expand=True)

        # Header
        header = tk.Frame(outer, bg=T.PANEL, height=30)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_font = tkfont.Font(family=T.FONT_MAIN, size=10, weight="bold")
        tk.Label(header, text=f"{Icon.LOGO}  Ask Luffi", font=title_font,
                 fg=T.WHITE, bg=T.PANEL, padx=14).pack(side="left", fill="y")

        close_btn = tk.Label(header, text=Icon.CLOSE, font=title_font,
                             fg=T.TEXT_MUTED, bg=T.PANEL, cursor="hand2", padx=10)
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Button-1>", lambda e: root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=T.WHITE))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=T.TEXT_MUTED))

        # Input row
        input_frame = tk.Frame(outer, bg=T.BG)
        input_frame.pack(fill="both", expand=True, padx=16, pady=10)

        prompt_font = tkfont.Font(family=T.FONT_MAIN, size=14, weight="bold")
        tk.Label(input_frame, text=Icon.ASK, font=prompt_font,
                 fg=T.WHITE, bg=T.BG).pack(side="left", padx=(0, 10))

        input_font = tkfont.Font(family=T.FONT_MAIN, size=13)
        entry = tk.Entry(
            input_frame, font=input_font,
            fg=T.TEXT, bg=T.CARD, bd=0,
            highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.WHITE, insertbackground=T.WHITE,
            selectbackground=T.PANEL_HOVER,
        )
        entry.pack(fill="both", expand=True, ipady=8, ipadx=8)
        entry.focus_force()

        hint_font = tkfont.Font(family=T.FONT_MAIN, size=8)
        tk.Label(outer, text="Enter to run    ·    Esc to cancel",
                 font=hint_font, fg=T.TEXT_MUTED, bg=T.BG).pack(
            side="bottom", anchor="w", padx=16, pady=(0, 6))

        def submit(e=None):
            text = entry.get().strip()
            root.destroy()
            if text and _result_callback:
                _result_callback(text)

        entry.bind("<Return>", submit)
        root.bind("<Escape>", lambda e: root.destroy())

        # Drag
        drag = {"x": 0, "y": 0}
        def start(e):
            drag["x"], drag["y"] = e.x, e.y
        def move(e):
            root.geometry(f"+{root.winfo_x() + e.x - drag['x']}+{root.winfo_y() + e.y - drag['y']}")
        header.bind("<Button-1>", start)
        header.bind("<B1-Motion>", move)

        root.mainloop()
