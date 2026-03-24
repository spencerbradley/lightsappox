#backend/models/preset.py
"""Model for Combined Presets"""
from pydantic import BaseModel

from paths import get_data_dir
from .device_presets import DEVICEPreset
from .ledfx_setting import LEDFXSetting
from .storage import load_optional


class Preset(BaseModel):
    id: str
    device_presets: list[str] = []
    ledfx_setting: str = ""

    model_config = {
        "json_schema_extra":{
        "example": {
            "id": "preset_1",
            "device_presets": ["Device1_Preset1", "Device2_Preset1"],
            "ledfx_setting": "ledfx_setting_1"
            }
        }
    }

    def get_id(self) -> str:
        return self.id

    def get_device_presets(self, filepath: str | None = None) -> list[DEVICEPreset]:
        filepath = filepath or str(get_data_dir() / "device_presets.json")
        all_presets = load_optional(filepath, DEVICEPreset)
        return [p for p in all_presets if p.get_id() in self.device_presets]

    def get_ledfx_setting(self, filepath: str | None = None) -> LEDFXSetting | None:
        filepath = filepath or str(get_data_dir() / "ledfx_settings.json")
        all_ledfx_settings = load_optional(filepath, LEDFXSetting)
        for setting in all_ledfx_settings:
            if setting.get_id() == self.ledfx_setting:
                return setting
        return None



