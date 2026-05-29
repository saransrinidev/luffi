import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from PIL import ImageGrab
    import easyocr
    OCR_AVAILABLE = True
    reader = None
except ImportError:
    OCR_AVAILABLE = False
    reader = None
    logger.warning("easyocr/Pillow not installed — OCR disabled")


class OCRService:
    """Capture screen region and extract text via OCR."""

    def __init__(self):
        global reader
        if OCR_AVAILABLE and reader is None:
            logger.info("Loading EasyOCR model (first time may take a moment)...")
            reader = easyocr.Reader(["en"], gpu=False)
            logger.info("EasyOCR ready")

    @staticmethod
    def capture_screen() -> str | None:
        """Capture full screen and extract text."""
        if not OCR_AVAILABLE:
            return None

        try:
            img = ImageGrab.grab()
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(tmp.name)

            results = reader.readtext(tmp.name)
            text = " ".join([r[1] for r in results])

            Path(tmp.name).unlink(missing_ok=True)
            return text.strip() if text.strip() else None
        except Exception as e:
            logger.error(f"OCR capture failed: {e}")
            return None

    @staticmethod
    def capture_region(x1: int, y1: int, x2: int, y2: int) -> str | None:
        """Capture a specific screen region and extract text."""
        if not OCR_AVAILABLE:
            return None

        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(tmp.name)

            results = reader.readtext(tmp.name)
            text = " ".join([r[1] for r in results])

            Path(tmp.name).unlink(missing_ok=True)
            return text.strip() if text.strip() else None
        except Exception as e:
            logger.error(f"OCR region capture failed: {e}")
            return None
