"""In-memory state for the active scene (beat-synced cycling)."""
_active = {"scene_id": None, "preset_ids": [], "current_index": 0}


def get_state():
    return {
        "scene_id": _active["scene_id"],
        "preset_ids": _active["preset_ids"].copy(),
        "current_index": _active["current_index"],
    }


def set_scene(scene_id: str, preset_ids: list[str]) -> None:
    _active["scene_id"] = scene_id
    _active["preset_ids"] = list(preset_ids) if preset_ids else []
    _active["current_index"] = 0


def clear_scene() -> None:
    _active["scene_id"] = None
    _active["preset_ids"] = []
    _active["current_index"] = 0


def advance_and_apply(apply_preset_fn) -> dict | None:
    """Advance to next preset in list and apply it (cycle). Returns result dict or None if no active scene."""
    if not _active["preset_ids"]:
        return None
    _active["current_index"] = (_active["current_index"] + 1) % len(_active["preset_ids"])
    idx = _active["current_index"]
    preset_id = _active["preset_ids"][idx]
    apply_preset_fn(preset_id)
    return {
        "applied": preset_id,
        "index": idx,
        "scene_id": _active["scene_id"],
    }
