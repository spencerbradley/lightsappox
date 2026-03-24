"""All DELETE routes."""
from fastapi import APIRouter, HTTPException

from routes.data import (
    load_device_presets,
    load_presets,
    load_scenes,
    save_device_presets,
    save_presets,
    save_scenes,
)

router = APIRouter(tags=["delete"])

# device-presets
device_presets_router = APIRouter(prefix="/device-presets")
@device_presets_router.delete("/{preset_id}")
def delete_device_preset(preset_id: str):
    presets = load_device_presets()
    for i, p in enumerate(presets):
        if p.get_id() == preset_id:
            presets.pop(i)
            save_device_presets(presets)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Device preset not found")
router.include_router(device_presets_router)

# presets
presets_router = APIRouter(prefix="/presets")
@presets_router.delete("/{preset_id}")
def delete_preset(preset_id: str):
    presets = load_presets()
    for i, p in enumerate(presets):
        if p.get_id() == preset_id:
            presets.pop(i)
            save_presets(presets)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Preset not found")
router.include_router(presets_router)

# scenes
scenes_router = APIRouter(prefix="/scenes")
@scenes_router.delete("/{scene_id}")
def delete_scene(scene_id: str):
    scenes = load_scenes()
    for i, s in enumerate(scenes):
        if s.id == scene_id:
            scenes.pop(i)
            save_scenes(scenes)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Scene not found")
router.include_router(scenes_router)
