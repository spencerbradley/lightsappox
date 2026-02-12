# backend/main.py
"""FastAPI Server"""
import asyncio
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

_BACKEND_DIR = Path(__file__).parent
_DATA_DIR = _BACKEND_DIR / "data"

sender = SENDER(str(_DATA_DIR / "config.json"))
running = True
status_loop_running = True


async def send_loop():
    while running:
        sender.send()
        await asyncio.sleep(0.001)  # ~30fps


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    send_task = asyncio.create_task(send_loop())
    status_task = asyncio.create_task(status_print_loop())
    yield
    global running, status_loop_running
    running = False
    status_loop_running = False
    send_task.cancel()
    status_task.cancel()
    try:
        await send_task
    except asyncio.CancelledError:
        pass
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

api = APIRouter(prefix="/api")
api.include_router(get.router)
api.include_router(post.router)
api.include_router(put.router)
api.include_router(delete.router)
app.include_router(api)

_frontend_dir = _BACKEND_DIR.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="static")

config = load_optional_single(str(_DATA_DIR / "config.json"), CONFIG)
if config is None:
    raise FileNotFoundError("config.json not found or invalid in data directory")
uvicorn.run(app, host=config.server_host, port=config.server_port)






