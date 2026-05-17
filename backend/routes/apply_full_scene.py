"""Apply a full scene (combined scene + optional ILDA scene)."""
from fastapi import HTTPException

from ilda.player import PLAYER
from routes.active_scene import set_full_scene
from routes.data import (
    get_ilda_scene_by_id,
    load_full_scenes,
    load_scenes,
)


def apply_full_scene_by_id(full_scene_id: str, apply_preset_fn) -> dict:
    full_scenes = load_full_scenes()
    full = next((f for f in full_scenes if f.id == full_scene_id), None)
    if not full:
        raise HTTPException(status_code=404, detail=f"Full scene not found: {full_scene_id}")

    scenes = load_scenes()
    scene = next((s for s in scenes if s.id == full.scene_id), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Combined scene not found: {full.scene_id}")

    preset_ids = getattr(scene, "preset_ids", None) or []
    ilda_scene = get_ilda_scene_by_id(full.ilda_scene_id) if full.ilda_scene_id else None

    set_full_scene(full.id, scene.id, preset_ids, full.ilda_scene_id or None)
    PLAYER.start_scene(ilda_scene)

    if preset_ids:
        apply_preset_fn(preset_ids[0])

    return {
        "status": "active",
        "full_scene_id": full.id,
        "scene_id": scene.id,
        "ilda_scene_id": full.ilda_scene_id or "",
        "preset_ids": preset_ids,
    }
