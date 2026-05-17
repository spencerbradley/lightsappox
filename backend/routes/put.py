"""All PUT (save/update) routes."""
from fastapi import APIRouter, HTTPException

from models.config import CONFIG
from models.device import DMXDevice
from models.device_presets import DEVICEPreset
from models.preset import Preset
from models.fullscene import FullScene
from models.ildaframe import IldaFrame
from models.ildascene import IldaScene
from models.scene import Scene
from routes.data import (
    get_data_dir,
    load_config,
    load_device_presets,
    load_devices,
    load_full_scenes,
    load_ilda_frames,
    load_ilda_scenes,
    load_presets,
    load_scenes,
    save_config,
    save_device_presets,
    save_devices,
    save_full_scenes,
    save_ilda_frames,
    save_ilda_scenes,
    save_presets,
    save_scenes,
)

router = APIRouter(tags=["put"])

# config
config_router = APIRouter(prefix="/config")
@config_router.put("")
def put_config(config: CONFIG):
    save_config(config)
    return config
router.include_router(config_router)

# devices
devices_router = APIRouter(prefix="/devices")
@devices_router.put("/{device_id}")
def put_device(device_id: str, device: DMXDevice):
    devices = load_devices()
    for i, d in enumerate(devices):
        if d.get_id() == device_id:
            devices[i] = device
            save_devices(devices)
            return device
    raise HTTPException(status_code=404, detail="Device not found")
@devices_router.put("/{device_id}/channels")
def put_device_channels(device_id: str, channels: list[int]):
    devices = load_devices()
    for i, d in enumerate(devices):
        if d.get_id() == device_id:
            devices[i] = d.model_copy(update={"active_channels": channels})
            save_devices(devices)
            return devices[i]
    raise HTTPException(status_code=404, detail="Device not found")
router.include_router(devices_router)

# device-presets
device_presets_router = APIRouter(prefix="/device-presets")
@device_presets_router.put("/{preset_id}")
def put_device_preset(preset_id: str, preset: DEVICEPreset):
    presets = load_device_presets()
    for i, p in enumerate(presets):
        if p.get_id() == preset_id:
            presets[i] = preset
            save_device_presets(presets)
            return preset
    raise HTTPException(status_code=404, detail="Device preset not found")
router.include_router(device_presets_router)

# presets
presets_router = APIRouter(prefix="/presets")
@presets_router.put("/{preset_id}")
def put_preset(preset_id: str, preset: Preset):
    presets = load_presets()
    for i, p in enumerate(presets):
        if p.get_id() == preset_id:
            presets[i] = preset
            save_presets(presets)
            return preset
    raise HTTPException(status_code=404, detail="Preset not found")
router.include_router(presets_router)

# scenes
scenes_router = APIRouter(prefix="/scenes")

@scenes_router.put("/reorder")
def put_scenes_reorder(body: dict):
    """Reorder scenes by passing list of scene ids in desired order."""
    scene_ids = body.get("scene_ids")
    if not isinstance(scene_ids, list) or len(scene_ids) == 0:
        raise HTTPException(status_code=400, detail="Body must contain 'scene_ids' (non-empty list)")
    scenes = load_scenes()
    id_to_scene = {s.id: s for s in scenes}
    ordered = []
    for sid in scene_ids:
        if sid in id_to_scene:
            ordered.append(id_to_scene[sid])
    if len(ordered) != len(scenes):
        raise HTTPException(status_code=400, detail="scene_ids must contain exactly the same scene ids as existing scenes")
    save_scenes(ordered)
    return {"scene_ids": [s.id for s in ordered]}

@scenes_router.put("/{scene_id}")
def put_scene(scene_id: str, scene: Scene):
    scenes = load_scenes()
    for i, s in enumerate(scenes):
        if s.id == scene_id:  # Scene has no get_id()
            scenes[i] = scene
            save_scenes(scenes)
            return scene
    raise HTTPException(status_code=404, detail="Scene not found")
router.include_router(scenes_router)

# ilda frames
ilda_frames_router = APIRouter(prefix="/ilda-frames")
@ilda_frames_router.put("/{frame_id}")
def put_ilda_frame(frame_id: str, frame: IldaFrame):
    frames = load_ilda_frames()
    for i, f in enumerate(frames):
        if f.id == frame_id:
            frames[i] = frame
            save_ilda_frames(frames)
            return frame
    raise HTTPException(status_code=404, detail="ILDA frame not found")
router.include_router(ilda_frames_router)

# ilda scenes
ilda_scenes_router = APIRouter(prefix="/ilda-scenes")
@ilda_scenes_router.put("/{scene_id}")
def put_ilda_scene(scene_id: str, scene: IldaScene):
    scenes = load_ilda_scenes()
    for i, s in enumerate(scenes):
        if s.id == scene_id:
            scenes[i] = scene
            save_ilda_scenes(scenes)
            return scene
    raise HTTPException(status_code=404, detail="ILDA scene not found")
router.include_router(ilda_scenes_router)

# full scenes
full_scenes_router = APIRouter(prefix="/full-scenes")

@full_scenes_router.put("/reorder")
def put_full_scenes_reorder(body: dict):
    scene_ids = body.get("scene_ids")
    if not isinstance(scene_ids, list) or len(scene_ids) == 0:
        raise HTTPException(status_code=400, detail="Body must contain 'scene_ids' (non-empty list)")
    scenes = load_full_scenes()
    id_to_scene = {s.id: s for s in scenes}
    ordered = [id_to_scene[sid] for sid in scene_ids if sid in id_to_scene]
    if len(ordered) != len(scenes):
        raise HTTPException(status_code=400, detail="scene_ids must contain exactly the same full scene ids as existing")
    save_full_scenes(ordered)
    return {"scene_ids": [s.id for s in ordered]}

@full_scenes_router.put("/{full_scene_id}")
def put_full_scene(full_scene_id: str, full_scene: FullScene):
    scenes = load_full_scenes()
    for i, s in enumerate(scenes):
        if s.id == full_scene_id:
            scenes[i] = full_scene
            save_full_scenes(scenes)
            return full_scene
    raise HTTPException(status_code=404, detail="Full scene not found")
router.include_router(full_scenes_router)

# ledfx (optional - fails silently when offline)
ledfx_router = APIRouter(prefix="/ledfx")
@ledfx_router.put("/active")
def put_ledfx_active(body: dict):
    scene_id = body.get("id")
    if not scene_id:
        raise HTTPException(status_code=400, detail="Missing 'id' in body")
    try:
        from ledfx.client import LEDFXClient
        client = LEDFXClient(str(get_data_dir() / "config.json"), port=8888)
        client.set_active_scene(scene_id)
        return {"active_scene": scene_id}
    except Exception:
        return {"active_scene": ""}
router.include_router(ledfx_router)
