# backend/main.py
"""FastAPI Server"""
import asyncio
import sys
import threading
from pathlib import Path
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models.config import CONFIG
from models.storage import load_optional_single
from dmx.sender import SENDER
import sacn

# Import early to init local data dir (avoids cloud sync wiping devices when wifi changes)
from routes.data import get_data_dir

if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent
    _FRONTEND_DIR = _BASE_DIR / "frontend"
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent
    _FRONTEND_DIR = _BASE_DIR / "frontend"

_DATA_DIR = get_data_dir()
print(f"[Main] Data dir: {_DATA_DIR}")
print("[Main] Creating DMX sender...")
sender = SENDER(str(_DATA_DIR / "config.json"))
print("[Main] DMX sender created successfully")
_dmx_sender_running = False
_dmx_sender_thread = None
status_loop_running = True


def dmx_sender_loop():
    """Background thread that continuously sends DMX data (matches lightsappnewgb pattern)."""
    global _dmx_sender_running
    print("[Main] DMX send loop started")
    loop_count = 0
    while _dmx_sender_running:
        try:
            sender.send()
            loop_count += 1
            if loop_count == 1:
                print("[Main] First send() call completed")
            # No sleep - let sacn library handle fps throttling internally
            # This matches the working pattern from lightsappnewgb
        except Exception as e:
            import time
            if not hasattr(dmx_sender_loop, '_last_error_time') or time.time() - dmx_sender_loop._last_error_time > 5:
                print(f"[Main] DMX send loop error: {e}")
                import traceback
                traceback.print_exc()
                dmx_sender_loop._last_error_time = time.time()
    print("[Main] DMX send loop stopped")


def _print_status_once():
    from routes.data import load_devices

    devices = load_devices()
    for d in devices:
        print(f"  {d.id}: active_channels = {d.active_channels}")
    try:
        from ledfx.client import LEDFXClient
        client = LEDFXClient(str(_DATA_DIR / "config.json"), port=8888)
        active = client.get_active_scene()
        print(f"  ledfx: {active or '(none)'}")
    except Exception as e:
        print(f"  ledfx: (error: {e})")


async def status_print_loop():
    while status_loop_running:
        await asyncio.sleep(1)
        if not status_loop_running:
            break
        print("--- active channels & ledfx ---")
        await asyncio.to_thread(_print_status_once)


def start_dmx_sender():
    """Start the DMX sender background thread."""
    global _dmx_sender_thread, _dmx_sender_running
    if _dmx_sender_thread and _dmx_sender_thread.is_alive():
        return
    _dmx_sender_running = True
    _dmx_sender_thread = threading.Thread(target=dmx_sender_loop, daemon=True)
    _dmx_sender_thread.start()


def stop_dmx_sender():
    """Stop the DMX sender background thread."""
    global _dmx_sender_running
    _dmx_sender_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_dmx_sender()
    status_task = asyncio.create_task(status_print_loop())
    yield
    global status_loop_running
    status_loop_running = False
    stop_dmx_sender()
    status_task.cancel()
    try:
        await status_task
    except asyncio.CancelledError:
        pass
    sender.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter
from routes import get, post, put, delete

# API routes must be registered before static mount so /api/* is not shadowed by StaticFiles.
api = APIRouter(prefix="/api")
api.include_router(get.router)
api.include_router(post.router)
api.include_router(put.router)
api.include_router(delete.router)

# AI mode routes (lazy import - routes will fail gracefully if dependencies unavailable)
try:
    from routes import ai_mode
    api.include_router(ai_mode.router, prefix="/ai-mode")
    print("[Main] AI mode routes registered")
except Exception as e:
    print(f"[Main] AI mode routes not available: {e}")
    print("[Main] Server will continue without AI mode. Install Visual C++ Redistributable if needed:")
    print("[Main] https://aka.ms/vs/17/release/vc_redist.x64.exe")
    # Don't print full traceback - just log that routes aren't available

app.include_router(api)

if _FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="static")

config = load_optional_single(str(_DATA_DIR / "config.json"), CONFIG)
if config is None:
    raise FileNotFoundError("config.json not found or invalid in data directory")
uvicorn.run(app, host=config.server_host, port=config.server_port)






