"""Shared load/save helpers for route handlers.
Data is stored in the local App Data directory only (e.g. %LOCALAPPDATA%\\LightsApp\\data on Windows)."""
from pathlib import Path

from models.config import CONFIG
from models.device import DMXDevice
from models.device_presets import DEVICEPreset
from models.preset import Preset
from models.scene import Scene
from models.storage import load_optional, load_optional_single, save, save_single
from paths import get_data_dir

_DATA_DIR = get_data_dir()
_DATA_DIR.mkdir(parents=True, exist_ok=True)

_CONFIG_FILE = _DATA_DIR / "config.json"
_DEVICES_FILE = _DATA_DIR / "devices.json"
_DEVICE_PRESETS_FILE = _DATA_DIR / "device_presets.json"
_PRESETS_FILE = _DATA_DIR / "presets.json"
_SCENES_FILE = _DATA_DIR / "scenes.json"


def load_config() -> CONFIG | None:
    """Load config from JSON. Returns None if file is missing or invalid."""
    return load_optional_single(str(_CONFIG_FILE), CONFIG)


def save_config(config: CONFIG) -> None:
    save_single(str(_CONFIG_FILE), config)


def _devices_from_presets_fallback() -> list[DMXDevice]:
    """Infer devices from device_presets when devices.json is missing/corrupt."""
    presets = load_optional(str(_DEVICE_PRESETS_FILE), DEVICEPreset)
    seen: dict[str, int] = {}
    for p in presets:
        if p.device not in seen:
            seen[p.device] = len(p.channel_values)
    devices = []
    for order, (device_id, ch_count) in enumerate(sorted(seen.items(), key=lambda x: x[0]), start=1):
        devices.append(DMXDevice(
            id=device_id,
            order=order,
            channels=ch_count,
            active_channels=[0] * ch_count,
            control_type="manual",
        ))
    return devices


def _ensure_haze_device(devices: list[DMXDevice]) -> list[DMXDevice]:
    """Ensure haze (manual, 2-channel) is in the list; append and persist if missing."""
    if any((d.id or "").lower() == "haze" for d in devices):
        return devices
    next_order = max((d.order for d in devices), default=0) + 1
    haze = DMXDevice(
        id="haze",
        order=next_order,
        channels=2,
        active_channels=[0, 0],
        control_type="manual",
    )
    out = devices + [haze]
    save(str(_DEVICES_FILE), out)
    print("[Data] Added missing haze device to devices.json")
    return out


def _ensure_default_scene_based_devices(devices: list[DMXDevice]) -> list[DMXDevice]:
    """Ensure at least two scene-based devices (gigbar, keobin) exist so presets/scenes pages work."""
    scene_based = [d for d in devices if ((d.control_type or "").lower() != "manual")]
    if scene_based:
        return devices
    existing_ids = {(d.id or "").lower() for d in devices}
    to_prepend: list[DMXDevice] = []
    if "gigbar" not in existing_ids:
        to_prepend.append(DMXDevice(
            id="gigbar",
            order=1,
            channels=24,
            active_channels=[0] * 24,
            control_type="scene based",
        ))
        existing_ids.add("gigbar")
    if "keobin" not in existing_ids:
        to_prepend.append(DMXDevice(
            id="keobin",
            order=2,
            channels=24,
            active_channels=[0] * 24,
            control_type="scene based",
        ))
        existing_ids.add("keobin")
    if not to_prepend:
        return devices
    manual = [d for d in devices if ((d.control_type or "").lower() == "manual")]
    reordered: list[DMXDevice] = []
    for i, d in enumerate(to_prepend + manual, start=1):
        reordered.append(d.model_copy(update={"order": i}))
    save(str(_DEVICES_FILE), reordered)
    print("[Data] Bootstrapped default scene-based devices (gigbar, keobin) for presets/scenes")
    return reordered


def _fix_gigbar_keobin_control_type(devices: list[DMXDevice]) -> list[DMXDevice]:
    """If gigbar or keobin exist with control_type manual, set to 'scene based' so apply preset works."""
    scene_device_ids = {"gigbar", "keobin"}
    changed = False
    out: list[DMXDevice] = []
    for d in devices:
        if (d.id or "").lower() in scene_device_ids and ((d.control_type or "").lower() == "manual"):
            out.append(d.model_copy(update={"control_type": "scene based"}))
            changed = True
        else:
            out.append(d)
    if changed:
        save(str(_DEVICES_FILE), out)
        print("[Data] Set gigbar/keobin control_type to 'scene based' so presets can apply")
    return out


def load_devices() -> list[DMXDevice]:
    devices = load_optional(str(_DEVICES_FILE), DMXDevice)
    if not devices:
        print("[Data] devices.json empty or unreadable - reconstructing from device_presets")
        devices = _devices_from_presets_fallback()
        if devices:
            save(str(_DEVICES_FILE), devices)
            print(f"[Data] Restored devices.json with {len(devices)} device(s)")
    devices = _ensure_haze_device(devices)
    devices = _ensure_default_scene_based_devices(devices)
    devices = _fix_gigbar_keobin_control_type(devices)
    return devices


def save_devices(devices: list[DMXDevice]) -> None:
    """Save devices. Never overwrite with empty list - prevents accidental wipe from load errors."""
    if not devices:
        print("[Data] Refusing to save_devices: empty list would erase devices.json")
        return
    save(str(_DEVICES_FILE), devices)


def load_device_presets() -> list[DEVICEPreset]:
    return load_optional(str(_DEVICE_PRESETS_FILE), DEVICEPreset)


def save_device_presets(presets: list[DEVICEPreset]) -> None:
    save(str(_DEVICE_PRESETS_FILE), presets)


def load_presets() -> list[Preset]:
    return load_optional(str(_PRESETS_FILE), Preset)


def save_presets(presets: list[Preset]) -> None:
    save(str(_PRESETS_FILE), presets)


def load_scenes() -> list[Scene]:
    return load_optional(str(_SCENES_FILE), Scene)


def save_scenes(scenes: list[Scene]) -> None:
    save(str(_SCENES_FILE), scenes)


def get_data_dir() -> Path:
    return _DATA_DIR


def get_device_presets_path() -> str:
    return str(_DEVICE_PRESETS_FILE)


def get_presets_path() -> str:
    return str(_PRESETS_FILE)
