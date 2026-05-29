import threading
import logging

logger = logging.getLogger(__name__)

try:
    from pystray import Icon, MenuItem, Menu
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logger.warning("pystray/Pillow not installed — tray icon disabled")


class TrayService:
    """System tray icon with status and quick actions."""

    def __init__(self, on_quit=None, on_model_switch=None):
        self.on_quit = on_quit
        self.on_model_switch = on_model_switch
        self.icon = None

    def start(self):
        if not TRAY_AVAILABLE:
            return
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _create_icon_image(self):
        """Create a simple cyan circle icon."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=(0, 212, 255, 230))
        draw.text((22, 18), "N", fill=(10, 10, 20, 255))
        return img

    def _run(self):
        menu = Menu(
            MenuItem("NAP — AI Assistant", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Switch Model", self._switch_model),
            MenuItem("Quit", self._quit),
        )

        self.icon = Icon("NAP", self._create_icon_image(), "NAP", menu)
        logger.info("System tray icon started")
        self.icon.run()

    def _switch_model(self):
        if self.on_model_switch:
            self.on_model_switch()

    def _quit(self):
        if self.icon:
            self.icon.stop()
        if self.on_quit:
            self.on_quit()
