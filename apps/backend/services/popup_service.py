"""
Result Popup — professional monochrome (black & white) design.
Persistent window that updates content. Stays until dismissed.
"""
import threading
import logging
import tkinter as tk
from tkinter import font as tkfont
import pyperclip
import queue

from services import theme as T
from services.theme import Icon

logger = logging.getLogger(__name__)

_message_queue = queue.Queue()
_popup_thread = None
_popup_ready = threading.Event()


class PopupService:
    """Monochrome result popup. Updates in place, stays open until closed."""

    @staticmethod
    def show(text: str, title: str = "Luffi"):
        global _popup_thread
        if _popup_thread is None or not _popup_thread.is_alive():
            _popup_ready.clear()
            _popup_thread = threading.Thread(target=PopupService._run_popup, daemon=False)
            _popup_thread.start()
            _popup_ready.wait(timeout=3)
        _message_queue.put({"text": text, "title": title})

    @staticmethod
    def _run_popup():
        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", T.ALPHA)

        width, height = 660, 430
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.configure(bg=T.BG)

        # Outer border
        outer = tk.Frame(root, bg=T.BG, highlightbackground=T.BORDER,
                         highlightthickness=1, bd=0)
        outer.pack(fill="both", expand=True)

        # Header
        header = tk.Frame(outer, bg=T.PANEL, height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo_font = tkfont.Font(family=T.FONT_MAIN, size=11, weight="bold")
        title_label = tk.Label(header, text=f"{Icon.LOGO}  Luffi", font=logo_font,
                               fg=T.WHITE, bg=T.PANEL, anchor="w", padx=14)
        title_label.pack(side="left", fill="y")

        sub_font = tkfont.Font(family=T.FONT_MAIN, size=9)
        subtitle_label = tk.Label(header, text="", font=sub_font,
                                  fg=T.TEXT_MUTED, bg=T.PANEL)
        subtitle_label.pack(side="left", fill="y")

        # Close button
        close_font = tkfont.Font(family=T.FONT_MAIN, size=12)
        close_btn = tk.Label(header, text=Icon.CLOSE, font=close_font,
                             fg=T.TEXT_MUTED, bg=T.PANEL, cursor="hand2", padx=12)
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Button-1>", lambda e: root.withdraw())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=T.WHITE))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=T.TEXT_MUTED))

        # Copy button
        copy_font = tkfont.Font(family=T.FONT_MAIN, size=9)
        copy_btn = tk.Label(header, text="Copy", font=copy_font,
                            fg=T.TEXT_MUTED, bg=T.PANEL, cursor="hand2", padx=10)
        copy_btn.pack(side="right", fill="y")

        current_text = [""]

        def copy_text(e=None):
            pyperclip.copy(current_text[0])
            copy_btn.config(text="Copied", fg=T.WHITE)
            root.after(1400, lambda: copy_btn.config(text="Copy", fg=T.TEXT_MUTED))

        copy_btn.bind("<Button-1>", copy_text)
        copy_btn.bind("<Enter>", lambda e: copy_btn.config(fg=T.WHITE))
        copy_btn.bind("<Leave>", lambda e: copy_btn.config(fg=T.TEXT_MUTED))

        # Divider
        tk.Frame(outer, bg=T.DIVIDER, height=1).pack(fill="x")

        # Content
        content = tk.Frame(outer, bg=T.BG)
        content.pack(fill="both", expand=True, padx=16, pady=12)

        scrollbar = tk.Scrollbar(content, bg=T.PANEL, troughcolor=T.BG,
                                 activebackground=T.BORDER, width=8,
                                 highlightthickness=0, bd=0)
        scrollbar.pack(side="right", fill="y")

        text_font = tkfont.Font(family=T.FONT_MAIN, size=11)
        text_widget = tk.Text(
            content, wrap="word", font=text_font,
            fg=T.TEXT, bg=T.BG, bd=0, highlightthickness=0,
            padx=4, pady=2, yscrollcommand=scrollbar.set,
            selectbackground=T.PANEL_HOVER, insertbackground=T.WHITE,
            spacing1=3, spacing3=3,
        )
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # Footer
        footer = tk.Frame(outer, bg=T.PANEL, height=24)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        hint_font = tkfont.Font(family=T.FONT_MAIN, size=8)
        tk.Label(footer, text="Esc to close   ·   Ctrl+C to copy selection",
                 font=hint_font, fg=T.TEXT_MUTED, bg=T.PANEL).pack(side="left", padx=12)

        root.bind("<Escape>", lambda e: root.withdraw())
        root.bind("<Control-c>", copy_text)

        # Drag
        drag = {"x": 0, "y": 0}
        def start_drag(e):
            drag["x"], drag["y"] = e.x, e.y
        def do_drag(e):
            root.geometry(f"+{root.winfo_x() + e.x - drag['x']}+{root.winfo_y() + e.y - drag['y']}")
        for w in (header, title_label):
            w.bind("<Button-1>", start_drag)
            w.bind("<B1-Motion>", do_drag)

        _popup_ready.set()

        def check_queue():
            try:
                while True:
                    msg = _message_queue.get_nowait()
                    text_content = msg["text"]
                    title_text = msg["title"]

                    current_text[0] = text_content
                    # Split "Luffi · mode · ..." subtitle
                    if "·" in title_text:
                        parts = title_text.split("·", 1)
                        subtitle_label.config(text="  " + parts[1].strip())
                    else:
                        subtitle_label.config(text="")

                    text_widget.config(state="normal")
                    text_widget.delete("1.0", "end")
                    text_widget.insert("1.0", text_content)
                    text_widget.config(state="disabled")

                    root.deiconify()
                    root.lift()
                    root.focus_force()
            except queue.Empty:
                pass
            root.after(100, check_queue)

        check_queue()
        root.mainloop()
