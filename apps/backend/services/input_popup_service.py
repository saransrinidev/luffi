import threading
import logging
import tkinter as tk
from tkinter import font as tkfont
import queue

logger = logging.getLogger(__name__)

_input_queue = queue.Queue()
_result_callback = None


class InputPopupService:
    """
    CMD-style input box popup. Opens on hotkey, user types a prompt,
    presses Enter, and it gets processed.
    """

    @staticmethod
    def show(callback):
        """Show input popup. callback(text) is called when user submits."""
        global _result_callback
        _result_callback = callback
        thread = threading.Thread(target=InputPopupService._create_input, daemon=False)
        thread.start()

    @staticmethod
    def _create_input():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.92)

        bg_color = "#0c0c0c"
        input_bg = "#1a1a1a"
        text_color = "#cccccc"
        accent = "#16c60c"
        border_color = "#333333"

        width = 600
        height = 120
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.configure(bg=bg_color)

        # Border
        outer = tk.Frame(root, bg=bg_color, highlightbackground=border_color,
                         highlightthickness=1, bd=0)
        outer.pack(fill="both", expand=True)

        # Header
        header = tk.Frame(outer, bg="#1a1a1a", height=28)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_font = tkfont.Font(family="Consolas", size=9, weight="bold")
        tk.Label(header, text="Luffi > Ask anything...", font=title_font,
                 fg=accent, bg="#1a1a1a", padx=10).pack(side="left", fill="y")

        # Close
        close_btn = tk.Label(header, text=" X ", font=title_font,
                             fg="#666666", bg="#1a1a1a", cursor="hand2")
        close_btn.pack(side="right", padx=4)
        close_btn.bind("<Button-1>", lambda e: root.destroy())

        # Input area
        input_frame = tk.Frame(outer, bg=bg_color)
        input_frame.pack(fill="both", expand=True, padx=12, pady=8)

        # Prompt symbol
        prompt_font = tkfont.Font(family="Consolas", size=11)
        tk.Label(input_frame, text=">", font=prompt_font,
                 fg=accent, bg=bg_color).pack(side="left", padx=(0, 6))

        # Input entry
        input_font = tkfont.Font(family="Consolas", size=11)
        entry = tk.Entry(
            input_frame, font=input_font,
            fg=text_color, bg=input_bg, bd=0,
            highlightthickness=1, highlightbackground="#333333",
            highlightcolor=accent,
            insertbackground=accent,
            selectbackground="#264f78",
        )
        entry.pack(fill="both", expand=True, ipady=6)
        entry.focus_force()

        # Hint
        hint_font = tkfont.Font(family="Consolas", size=7)
        tk.Label(outer, text=" ENTER submit | ESC cancel | Try: 'screenshot and summarize' or 'analyse this page'",
                 font=hint_font, fg="#444444", bg=bg_color).pack(side="bottom", anchor="w", padx=12, pady=(0, 4))

        def submit(e=None):
            text = entry.get().strip()
            root.destroy()
            if text and _result_callback:
                _result_callback(text)

        entry.bind("<Return>", submit)
        root.bind("<Escape>", lambda e: root.destroy())

        # Draggable header
        drag = {"x": 0, "y": 0}

        def start_drag(e):
            drag["x"] = e.x
            drag["y"] = e.y

        def do_drag(e):
            root.geometry(f"+{root.winfo_x() + e.x - drag['x']}+{root.winfo_y() + e.y - drag['y']}")

        header.bind("<Button-1>", start_drag)
        header.bind("<B1-Motion>", do_drag)

        root.mainloop()
