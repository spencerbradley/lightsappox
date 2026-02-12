"""All POST (create / apply) routes."""
from fastapi import APIRouter, HTTPException

from models.device_presets import DEVICEPreset
from models.preset import Preset
from models.scene import Scene
from routes.active_scene import advance_and_apply, clear_scene, get_state, set_scene
from routes.data import (
    get_data_dir,
    get_device_presets_path,
    get_presets_path,
    load_device_presets,
    load_devices,
    load_presets,
    load_scenes,
    save_devices,
    save_device_presets,
    save_presets,
    save_scenes,
)

router = APIRouter(tags=["post"])


def _apply_preset_by_id(preset_id: str) -> None:
    presets = load_presets()
    preset = next((p for p in presets if p.get_id() == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    device_presets = preset.get_device_presets(get_device_presets_path())
    devices = load_devices()
    for dp in device_presets:
        for i, d in enumerate(devices):
            if d.get_id() == dp.get_device():
                devices[i] = d.model_copy(update={"active_channels": dp.get_channel_values()})
                break
    save_devices(devices)
    if getattr(preset, "ledfx_setting", None) and preset.ledfx_setting.strip():
        try:
            from ledfx.client import LEDFXClient
            ledfx = LEDFXClient(str(get_data_dir() / "config.json"), port=8888)
            ledfx.set_active_scene(preset.ledfx_setting.strip())
        except Exception:
            pass


# device-presets: create (upsert — update if same id+device exists)
device_presets_router = APIRouter(prefix="/device-presets")
@device_presets_router.post("")
def post_device_preset(preset: DEVICEPreset):
    presets = load_device_presets()
    for i, p in enumerate(presets):
        if p.get_id() == preset.get_id() and p.get_device() == preset.get_device():
            presets[i] = preset
            save_device_presets(presets)
            return preset
    presets.append(preset)
    save_device_presets(presets)
    return preset
router.include_router(device_presets_router)

# presets: create
presets_router = APIRouter(prefix="/presets")
@presets_router.post("")
def post_preset(preset: Preset):
    presets = load_presets()
    presets.append(preset)
    save_presets(presets)
    return preset
router.include_router(presets_router)

# scenes: create
scenes_router = APIRouter(prefix="/scenes")
@scenes_router.post("")
def post_scene(scene: Scene):
    scenes = load_scenes()
    scenes.append(scene)
    save_scenes(scenes)
    return scene
router.include_router(scenes_router)

# apply
apply_router = APIRouter(prefix="/apply")
@apply_router.post("/device-preset/{device_id}/{preset_id}")
def post_apply_device_preset(device_id: str, preset_id: str):
    devices = load_devices()
    device_presets = load_device_presets()
    if not next((p for p in device_presets if p.get_device() == device_id and p.get_id() == preset_id), None):
        raise HTTPException(status_code=404, detail="Device preset not found")
    for i, d in enumerate(devices):
        if d.get_id() == device_id:
            d.set_active_channels(preset_id, presets=device_presets)
            devices[i] = d
            save_devices(devices)
            return {"status": "applied", "device_id": device_id, "preset_id": preset_id}
    raise HTTPException(status_code=404, detail="Device not found")

@apply_router.post("/preset/{preset_id}")
def post_apply_preset(preset_id: str):
    _apply_preset_by_id(preset_id)
    return {"status": "applied", "preset_id": preset_id}

@apply_router.post("/scene/{scene_id}")
def post_apply_scene(scene_id: str):
    """Set this scene as the active scene. It will cycle presets on each beat (advance)."""
    scenes = load_scenes()
    scene = next((s for s in scenes if s.id == scene_id), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    preset_ids = getattr(scene, "preset_ids", None) or []
    set_scene(scene_id, preset_ids)
    if preset_ids:
        _apply_preset_by_id(preset_ids[0])
    return {"status": "active", "scene_id": scene_id, "preset_ids": preset_ids}


# active-scene: set/clear and advance (called on each beat from frontend)
active_scene_router = APIRouter(prefix="/active-scene")
@active_scene_router.post("")
def post_active_scene(body: dict):
    """Set or clear the active scene. Body: { scene_id, preset_ids } or { scene_id: null } to clear."""
    if body.get("scene_id") is None or not body.get("preset_ids"):
        clear_scene()
        return get_state()
    set_scene(body["scene_id"], body.get("preset_ids", []))
    return get_state()


@active_scene_router.post("/advance")
def post_active_scene_advance():
    """Apply the current preset in the active scene, then advance to the next (for next beat)."""
    result = advance_and_apply(_apply_preset_by_id)
    if result is None:
        return {"status": "no_active_scene"}
    return {"status": "applied", **result}


router.include_router(active_scene_router)
router.include_router(apply_router)
