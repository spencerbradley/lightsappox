"""In-memory state for the active full scene (beat-synced preset + ILDA cycling)."""
_active = {
    "full_scene_id": None,
    "scene_id": None,
    "ilda_scene_id": None,
    "preset_ids": [],
    "current_index": 0,
}


def get_state() -> dict:
    from ilda.player import PLAYER

    return {
        "full_scene_id": _active["full_scene_id"],
        "scene_id": _active["scene_id"],
        "ilda_scene_id": _active["ilda_scene_id"],
        "preset_ids": _active["preset_ids"].copy(),
        "current_index": _active["current_index"],
        "ilda": PLAYER.get_state(),
    }


def set_full_scene(
    full_scene_id: str,
    scene_id: str,
    preset_ids: list[str],
    ilda_scene_id: str | None = None,
) -> None:
    _active["full_scene_id"] = full_scene_id
    _active["scene_id"] = scene_id
    _active["ilda_scene_id"] = ilda_scene_id or None
    _active["preset_ids"] = list(preset_ids) if preset_ids else []
    _active["current_index"] = 0


def clear_scene() -> None:
    from ilda.player import PLAYER

    _active["full_scene_id"] = None
    _active["scene_id"] = None
    _active["ilda_scene_id"] = None
    _active["preset_ids"] = []
    _active["current_index"] = 0
    PLAYER.stop()


def advance_and_apply(apply_preset_fn) -> dict | None:
    """Advance preset list and ILDA frames on beat. Returns result dict or None."""
    from ilda.player import PLAYER

    if not _active["preset_ids"] and not _active["ilda_scene_id"]:
        return None

    applied_preset = None
    if _active["preset_ids"]:
        _active["current_index"] = (_active["current_index"] + 1) % len(_active["preset_ids"])
        idx = _active["current_index"]
        preset_id = _active["preset_ids"][idx]
        apply_preset_fn(preset_id)
        applied_preset = preset_id

    applied_ilda_frame = None
    if PLAYER.is_beat_synced():
        applied_ilda_frame = PLAYER.advance_beat()

    return {
        "applied": applied_preset,
        "ilda_frame": applied_ilda_frame,
        "index": _active["current_index"],
        "full_scene_id": _active["full_scene_id"],
        "scene_id": _active["scene_id"],
    }
