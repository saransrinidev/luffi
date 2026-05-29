import uvicorn
import logging
import threading
import signal
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes import router
from services.hotkey_service import HotkeyService
from services.tray_service import TrayService
from services.model_service import ModelService

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Luffi Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

model_service = ModelService()


@app.on_event("startup")
async def startup_event():
    logger.info("Luffi Backend starting up...")

    # Start hotkey listener
    hotkey_service = HotkeyService()
    hotkey_thread = threading.Thread(target=hotkey_service.start, daemon=True)
    hotkey_thread.start()

    # Start system tray
    tray = TrayService(
        on_quit=lambda: sys.exit(0),
        on_model_switch=model_service.cycle_next,
    )
    tray.start()

    logger.info("All services started")


if __name__ == "__main__":
    # Ignore SIGINT so Ctrl+C doesn't kill the server
    # Stop with: Ctrl+Break or close this terminal
    import os
    if os.name == "nt":
        # On Windows, disable Ctrl+C handler entirely
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCtrlHandler(None, True)

    print("\n🚀 Luffi Backend starting...")
    print("   Stop with: Ctrl+Break or close this terminal\n")

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
