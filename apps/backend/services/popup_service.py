import threading
import logging
import tkinter as tk
from tkinter import font as tkfont
import pyperclip

logger = logging.getLogger(__name__)

_popup_instance = None


class PopupService:
    """Futuristic transparent blur popup centered on screen."""

    @staticmethod
    def show(text: str, title: str = "NAP"):
        """Show popup with text centered on screen."""
        thread = threading.Thread(
            target=PopupService._create_popup, args=(text, title), daemon=True
        )
        thread.start()

    @staticmethod
    def _create_popup(text: str, title: str):
        global _popup_instance

        # Close existing popup
        if _popup_instance:
            try:
                _popup_instance.destroy()
            except Exception:
                pass

        root = tk.Tk()
        _popup_instance = root

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.93)

        # Size and center
        width = 650
        height = 420
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.configure(bg="#08080d")

        # Outer glow border
        outer = tk.Frame(root, bg="#0f0f1a", highlightbackground="#00d4ff",
                         highlightthickness=1, bd=0)
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        inner = tk.Frame(outer, bg="#0b0b14")
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Header bar
        header = tk.Frame(inner, bg="#0b0b14", height=38)
        header.pack(fill="x", padx=16, pady=(10, 0))
        header.pack_propagate(False)

        title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        tk.Label(header, text=f"⚡ {title}", font=title_font,
                 fg="#00d4ff", bg="#0b0b14", anchor="w").pack(side="left", fill="y")

        # Close button
        close_font = tkfont.Font(family="Segoe UI", size=13)
        close_btn = tk.Label(header, text="✕", font=close_font,
                             fg="#555570", bg="#0b0b14", cursor="hand2")
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Button-1>", lambda e: root.destroy())

        # Copy button
        copy_font = tkfont.Font(family="Segoe UI", size=9)
        copy_btn = tk.Label(header, text="📋 Copy", font=copy_font,
                            fg="#555570", bg="#0b0b14", cursor="hand2", padx=8)
        copy_btn.pack(side="right", fill="y")

        def copy_text(e=None):
            pyperclip.copy(text)
            copy_btn.config(text="✅ Copied!", fg="#00d4ff")
            root.after(1500, lambda: copy_btn.config(text="📋 Copy", fg="#555570"))

        copy_btn.bind("<Button-1>", copy_text)

        # Separator
        tk.Frame(inner, bg="#1a1a3e", height=1).pack(fill="x", padx=16, pady=(6, 0))

        # Content
        content = tk.Frame(inner, bg="#0b0b14")
        content.pack(fill="both", expand=True, padx=16, pady=10)

        scrollbar = tk.Scrollbar(content, bg="#1a1a2e", troughcolor="#0b0b14", width=6)
        scrollbar.pack(side="right", fill="y")

        text_font = tkfont.Font(family="Cascadia Code", size=10)
        text_widget = tk.Text(
            content, wrap="word", font=text_font,
            fg="#e0e0f0", bg="#0b0b14", bd=0,
            highlightthickness=0, padx=6, pady=4,
            yscrollcommand=scrollbar.set,
            selectbackground="#1a3a5e",
            insertbackground="#00d4ff",
        )
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert("1.0", text)
        text_widget.config(state="disabled")

        # Footer
        footer = tk.Frame(inner, bg="#0b0b14", height=22)
        footer.pack(fill="x", padx=16, pady=(0, 8))
        footer.pack_propagate(False)

        hint_font = tkfont.Font(family="Segoe UI", size=8)
        tk.Label(footer, text="Esc to close · Ctrl+C to copy selection",
                 font=hint_font, fg="#333348", bg="#0b0b14").pack(side="left")

        # Keybindings
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<Control-c>", copy_text)
        root.focus_force()
        root.mainloop()
