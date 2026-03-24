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
    devices = load_devices()
    all_device_presets = load_device_presets()
    # Preset form sends one chosen preset id per scene-based device, in device order.
    # Apply by position so each device gets its chosen preset (avoids "blackout" overwriting "paruv" when both ids exist for different devices).
    scene_based = [d for d in devices if (getattr(d, "control_type", "") or "").lower() != "manual"]
    chosen_ids = getattr(preset, "device_presets", None) or []
    # Normalize for matching: case-insensitive, strip whitespace
    def norm(s: str) -> str:
        return (s or "").strip().lower()
    print(f"[Apply] preset {preset_id!r} device_presets={chosen_ids!r}, scene_based devices={[d.get_id() for d in scene_based]!r}, all_device_preset (device,id)={[(p.get_device(), p.get_id()) for p in all_device_presets]!r}")
    updated_any = False
    for i, d in enumerate(scene_based):
        if i >= len(chosen_ids) or not (chosen_ids[i] and str(chosen_ids[i]).strip()):
            print(f"[Apply] skip device index {i} (no chosen_id or empty)")
            continue
        preset_id_for_device = (chosen_ids[i] or "").strip()
        device_id_norm = norm(d.get_id())
        dp = next(
            (p for p in all_device_presets if norm(p.get_device()) == device_id_norm and norm(p.get_id()) == norm(preset_id_for_device)),
            None,
        )
        if not dp:
            print(f"[Apply] no device preset found for device={d.get_id()!r} id={preset_id_for_device!r}")
            continue
        ch_vals = list(dp.get_channel_values())
        for j, dev in enumerate(devices):
            if norm(dev.get_id()) == device_id_norm:
                devices[j] = dev.model_copy(update={"active_channels": ch_vals})
                updated_any = True
                print(f"[Apply] set device {d.get_id()!r} active_channels (len={len(ch_vals)})")
                break
    if not updated_any:
        print("[Apply] WARNING: no devices were updated (check device_presets order and device preset ids)")
    save_devices(devices)
    if getattr(preset, "ledfx_setting", None) and preset.ledfx_setting.strip():
        try:
            from ledfx.client import LEDFXClient
            ledfx = LEDFXClient(str(get_data_dir() / "config.json"), port=8888)
            scene_id = preset.ledfx_setting.strip()
            print(f"[LedFx] Attempting to activate scene: {scene_id}")
            ledfx.set_active_scene(scene_id)
            print(f"[LedFx] Successfully activated scene: {scene_id}")
        except Exception as e:
            # Print error so it's visible in terminal
            print(f"[LedFx] ERROR: Failed to set LedFx scene '{preset.ledfx_setting}': {e}")
            import traceback
            traceback.print_exc()


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
    print("[Apply] DEBUG: POST /api/apply/preset received — preset_id =", repr(preset_id))
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
    print("[Beat] Advance endpoint called")
    result = advance_and_apply(_apply_preset_by_id)
    if result is None:
        print("[Beat] No active scene")
        return {"status": "no_active_scene"}
    print(f"[Beat] Applied preset: {result.get('applied')} (index {result.get('index')})")
    return {"status": "applied", **result}


router.include_router(active_scene_router)
router.include_router(apply_router)
