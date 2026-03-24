"""Single source of truth for data directory. All app data lives in AppData/Local (Windows) or ~/.local/share (Unix), never in the backend folder."""
import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    """App Data dir: %LOCALAPPDATA%\\LightsApp\\data (Windows) or ~/.local/share/LightsApp/data (Unix)."""
    if os.environ.get("LIGHTSAPP_DATA_DIR"):
        return Path(os.environ["LIGHTSAPP_DATA_DIR"]).resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        base = Path.home() / ".local" / "share"
    return (base / "LightsApp" / "data").resolve()
