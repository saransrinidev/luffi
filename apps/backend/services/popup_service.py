import threading
import logging
import tkinter as tk
from tkinter import font as tkfont
import pyperclip
import queue

logger = logging.getLogger(__name__)

# Thread-safe queue to send messages to the popup
_message_queue = queue.Queue()
_popup_thread = None
_popup_ready = threading.Event()


class PopupService:
    """
    CMD-style black transparent popup. Stays open until user closes it.
    Uses a persistent thread with message queue to avoid race conditions.
    """

    @staticmethod
    def show(text: str, title: str = "Luffi"):
        """Show or update the popup with new content."""
        global _popup_thread

        # Start popup thread if not running
        if _popup_thread is None or not _popup_thread.is_alive():
            _popup_ready.clear()
            _popup_thread = threading.Thread(target=PopupService._run_popup, daemon=False)
            _popup_thread.start()
            _popup_ready.wait(timeout=3)

        # Send message to popup
        _message_queue.put({"text": text, "title": title})

    @staticmethod
    def _run_popup():
        global _popup_thread

        root = tk.Tk()
        root.withdraw()  # Hide until first message

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.90)

        # CMD-style: pure black
        bg_color = "#0c0c0c"
        text_color = "#cccccc"
        title_color = "#16c60c"  # Green like CMD
        border_color = "#333333"

        # Size and center
        width = 680
        height = 440
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.configure(bg=bg_color)

        # Border frame
        outer = tk.Frame(root, bg=bg_color, highlightbackground=border_color,
                         highlightthickness=1, bd=0)
        outer.pack(fill="both", expand=True)

        # Header bar
        header = tk.Frame(outer, bg="#1a1a1a", height=32)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_font = tkfont.Font(family="Consolas", size=9, weight="bold")
        title_label = tk.Label(header, text="Luffi", font=title_font,
                               fg=title_color, bg="#1a1a1a", anchor="w", padx=10)
        title_label.pack(side="left", fill="y")

        # Close button
        close_font = tkfont.Font(family="Consolas", size=11)
        close_btn = tk.Label(header, text=" X ", font=close_font,
                             fg="#999999", bg="#1a1a1a", cursor="hand2")
        close_btn.pack(side="right", fill="y", padx=4)

        def close_popup(e=None):
            root.withdraw()

        def close_btn_hover(e):
            close_btn.config(bg="#c42b1c", fg="#ffffff")

        def close_btn_leave(e):
            close_btn.config(bg="#1a1a1a", fg="#999999")

        close_btn.bind("<Button-1>", close_popup)
        close_btn.bind("<Enter>", close_btn_hover)
        close_btn.bind("<Leave>", close_btn_leave)

        # Copy button
        copy_font = tkfont.Font(family="Consolas", size=8)
        copy_btn = tk.Label(header, text="[COPY]", font=copy_font,
                            fg="#666666", bg="#1a1a1a", cursor="hand2", padx=6)
        copy_btn.pack(side="right", fill="y")

        current_text = [""]

        def copy_text(e=None):
            pyperclip.copy(current_text[0])
            copy_btn.config(text="[COPIED]", fg=title_color)
            root.after(1500, lambda: copy_btn.config(text="[COPY]", fg="#666666"))

        copy_btn.bind("<Button-1>", copy_text)

        # Content area
        content = tk.Frame(outer, bg=bg_color)
        content.pack(fill="both", expand=True, padx=12, pady=8)

        scrollbar = tk.Scrollbar(content, bg="#222222", troughcolor=bg_color,
                                 activebackground="#444444", width=8)
        scrollbar.pack(side="right", fill="y")

        text_font = tkfont.Font(family="Consolas", size=10)
        text_widget = tk.Text(
            content, wrap="word", font=text_font,
            fg=text_color, bg=bg_color, bd=0,
            highlightthickness=0, padx=8, pady=6,
            yscrollcommand=scrollbar.set,
            selectbackground="#264f78",
            insertbackground=title_color,
            spacing1=2, spacing3=2,
        )
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # Footer
        footer = tk.Frame(outer, bg="#1a1a1a", height=20)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        hint_font = tkfont.Font(family="Consolas", size=7)
        tk.Label(footer, text=" ESC close | Ctrl+C copy",
                 font=hint_font, fg="#555555", bg="#1a1a1a").pack(side="left", padx=8)

        # Keybindings
        root.bind("<Escape>", close_popup)
        root.bind("<Control-c>", copy_text)

        # Allow dragging the window
        drag_data = {"x": 0, "y": 0}

        def start_drag(e):
            drag_data["x"] = e.x
            drag_data["y"] = e.y

        def do_drag(e):
            dx = e.x - drag_data["x"]
            dy = e.y - drag_data["y"]
            new_x = root.winfo_x() + dx
            new_y = root.winfo_y() + dy
            root.geometry(f"+{new_x}+{new_y}")

        header.bind("<Button-1>", start_drag)
        header.bind("<B1-Motion>", do_drag)
        title_label.bind("<Button-1>", start_drag)
        title_label.bind("<B1-Motion>", do_drag)

        # Signal that popup is ready
        _popup_ready.set()

        def check_queue():
            """Poll for new messages."""
            try:
                while True:
                    msg = _message_queue.get_nowait()
                    text_content = msg["text"]
                    title_text = msg["title"]

                    current_text[0] = text_content
                    title_label.config(text=title_text)

                    text_widget.config(state="normal")
                    text_widget.delete("1.0", "end")
                    text_widget.insert("1.0", text_content)
                    text_widget.config(state="disabled")

                    # Show and bring to front
                    root.deiconify()
                    root.lift()
                    root.focus_force()

            except queue.Empty:
                pass

            root.after(100, check_queue)

        check_queue()
        root.mainloop()
