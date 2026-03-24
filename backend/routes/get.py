"""All GET (load) routes."""
from fastapi import APIRouter, HTTPException

from routes.active_scene import get_state as get_active_scene_state
from routes.data import (
    get_data_dir,
    load_config,
    load_device_presets,
    load_devices,
    load_presets,
    load_scenes,
)

router = APIRouter(tags=["get"])

# health
health_router = APIRouter()
@health_router.get("/health")
def get_health():
    return {"status": "ok"}
router.include_router(health_router)

# config
config_router = APIRouter(prefix="/config")
@config_router.get("")
def get_config():
    return load_config()
router.include_router(config_router)

# devices
devices_router = APIRouter(prefix="/devices")
@devices_router.get("")
def get_devices():
    return load_devices()
@devices_router.get("/{device_id}")
def get_device(device_id: str):
    devices = load_devices()
    for d in devices:
        if d.get_id() == device_id:
            return d
    raise HTTPException(status_code=404, detail="Device not found")
router.include_router(devices_router)

# device-presets
device_presets_router = APIRouter(prefix="/device-presets")
@device_presets_router.get("")
def get_device_presets():
    return load_device_presets()
router.include_router(device_presets_router)

# presets
presets_router = APIRouter(prefix="/presets")
@presets_router.get("")
def get_presets():
    return load_presets()
@presets_router.get("/{preset_id}")
def get_preset(preset_id: str):
    presets = load_presets()
    for p in presets:
        if p.get_id() == preset_id:
            return p
    raise HTTPException(status_code=404, detail="Preset not found")
router.include_router(presets_router)

# scenes
scenes_router = APIRouter(prefix="/scenes")
@scenes_router.get("")
def get_scenes():
    return load_scenes()
@scenes_router.get("/{scene_id}")
def get_scene(scene_id: str):
    scenes = load_scenes()
    for s in scenes:
        if s.id == scene_id:  # Scene has no get_id()
            return s
    raise HTTPException(status_code=404, detail="Scene not found")
router.include_router(scenes_router)

# ledfx (optional - returns empty when offline, zero wifi dependence)
ledfx_router = APIRouter(prefix="/ledfx")
@ledfx_router.get("/scenes")
def get_ledfx_scenes():
    try:
        from ledfx.client import LEDFXClient
        client = LEDFXClient(str(get_data_dir() / "config.json"), port=8888)
        return client.get_scenes()
    except Exception:
        return {"scenes": {}}
@ledfx_router.get("/active")
def get_ledfx_active():
    try:
        from ledfx.client import LEDFXClient
        client = LEDFXClient(str(get_data_dir() / "config.json"), port=8888)
        return {"active_scene": client.get_active_scene()}
    except Exception:
        return {"active_scene": ""}
router.include_router(ledfx_router)

# active scene (beat-synced cycling)
active_scene_router = APIRouter(prefix="/active-scene")
@active_scene_router.get("")
def get_active_scene():
    return get_active_scene_state()
router.include_router(active_scene_router)
