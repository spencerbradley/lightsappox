#backend/models/scene.py
"""Model for Scenes"""
from pydantic import BaseModel

from paths import get_data_dir
from .preset import Preset
from .storage import load_optional


class Scene(BaseModel):
    id: str
    preset_ids: list[str] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "scene_1",
                "preset_ids": ["preset_1", "preset_2"],
            }
        }
    }

    def get_presets(self, filepath: str | None = None) -> list[Preset]:
        filepath = filepath or str(get_data_dir() / "presets.json")
        all_presets = load_optional(filepath, Preset)
        return [p for p in all_presets if p.get_id() in self.preset_ids]



