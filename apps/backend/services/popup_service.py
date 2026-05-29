import threading
import logging
import tkinter as tk
from tkinter import font as tkfont

logger = logging.getLogger(__name__)

_popup_instance = None


class PopupService:
    """Futuristic transparent blur popup centered on screen."""

    @staticmethod
    def show(text: str, title: str = "NAP"):
        """Show popup with explanation text centered on screen."""
        thread = threading.Thread(target=PopupService._create_popup, args=(text, title), daemon=True)
        thread.start()

    @staticmethod
    def _create_popup(text: str, title: str):
        global _popup_instance

        root = tk.Tk()
        _popup_instance = root

        # Window setup
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.92)

        # Size and center
        width = 600
        height = 400
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")

        # Dark futuristic background
        root.configure(bg="#0a0a0f")

        # Main frame with border glow effect
        outer_frame = tk.Frame(root, bg="#1a1a2e", highlightbackground="#00d4ff",
                               highlightthickness=1, bd=0)
        outer_frame.pack(fill="both", expand=True, padx=2, pady=2)

        inner_frame = tk.Frame(outer_frame, bg="#0d0d1a")
        inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Header
        header = tk.Frame(inner_frame, bg="#0d0d1a", height=40)
        header.pack(fill="x", padx=16, pady=(12, 0))
        header.pack_propagate(False)

        title_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        title_label = tk.Label(header, text=f"⚡ {title}", font=title_font,
                               fg="#00d4ff", bg="#0d0d1a", anchor="w")
        title_label.pack(side="left", fill="y")

        # Close button
        close_font = tkfont.Font(family="Segoe UI", size=14)
        close_btn = tk.Label(header, text="✕", font=close_font,
                             fg="#666680", bg="#0d0d1a", cursor="hand2")
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Button-1>", lambda e: root.destroy())

        # Separator line
        sep = tk.Frame(inner_frame, bg="#1a1a3e", height=1)
        sep.pack(fill="x", padx=16, pady=(8, 0))

        # Content area with scroll
        content_frame = tk.Frame(inner_frame, bg="#0d0d1a")
        content_frame.pack(fill="both", expand=True, padx=16, pady=12)

        # Scrollbar
        scrollbar = tk.Scrollbar(content_frame, bg="#1a1a2e",
                                 troughcolor="#0d0d1a", width=8)
        scrollbar.pack(side="right", fill="y")

        # Text widget
        text_font = tkfont.Font(family="Cascadia Code", size=10)
        text_widget = tk.Text(content_frame, wrap="word", font=text_font,
                              fg="#e0e0f0", bg="#0d0d1a", bd=0,
                              highlightthickness=0, padx=4, pady=4,
                              yscrollcommand=scrollbar.set,
                              selectbackground="#1a3a5e",
                              insertbackground="#00d4ff")
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert("1.0", text)
        text_widget.config(state="disabled")

        # Footer hint
        footer = tk.Frame(inner_frame, bg="#0d0d1a", height=24)
        footer.pack(fill="x", padx=16, pady=(0, 8))
        footer.pack_propagate(False)

        hint_font = tkfont.Font(family="Segoe UI", size=8)
        hint = tk.Label(footer, text="Press Escape or click ✕ to close",
                        font=hint_font, fg="#444460", bg="#0d0d1a")
        hint.pack(side="left")

        # Keybindings
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<Button-1>", lambda e: root.focus_force())

        # Focus
        root.focus_force()
        root.mainloop()
