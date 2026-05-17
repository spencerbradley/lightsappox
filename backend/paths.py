"""Single source of truth for data directory. All app data lives in AppData/Local (Windows) or ~/.local/share (Unix), never in the backend folder."""
import os
import shutil
import sys
from pathlib import Path

from models.config import CONFIG
from models.storage import save_single

_DATA_FILENAMES = (
    "config.json",
    "devices.json",
    "device_presets.json",
    "presets.json",
    "scenes.json",
    "ilda_frames.json",
    "ilda_scenes.json",
    "full_scenes.json",
)


def get_data_dir() -> Path:
    """App Data dir: %LOCALAPPDATA%\\LightsApp\\data (Windows) or ~/.local/share/LightsApp/data (Unix)."""
    if os.environ.get("LIGHTSAPP_DATA_DIR"):
        return Path(os.environ["LIGHTSAPP_DATA_DIR"]).resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        base = Path.home() / ".local" / "share"
    return (base / "LightsApp" / "data").resolve()


def default_config() -> CONFIG:
    return CONFIG(
        id="config1",
        total_channels=512,
        IP="127.0.0.1",
        sacn_port=5568,
        priority=100,
        universe=1,
        server_host="127.0.0.1",
        server_port=8000,
        ai_mode_enabled=False,
    )


def ensure_data_initialized(seed_dir: Path | None = None) -> Path:
    """Create data dir and seed config/JSON files on first run."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    if seed_dir and seed_dir.is_dir():
        for name in _DATA_FILENAMES:
            src = seed_dir / name
            dst = data_dir / name
            if src.is_file() and not dst.exists():
                shutil.copy2(src, dst)
                print(f"[Paths] Copied {name} from {seed_dir}")

    config_path = data_dir / "config.json"
    if not config_path.is_file():
        save_single(str(config_path), default_config())
        print(f"[Paths] Created default config at {config_path}")

    for name in _DATA_FILENAMES:
        if name == "config.json":
            continue
        path = data_dir / name
        if not path.is_file():
            path.write_text("[]\n", encoding="utf-8")

    return data_dir
