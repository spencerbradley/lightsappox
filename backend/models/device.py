#backend/models/device.py
"""DMX Presets Page"""

from pydantic import BaseModel

from paths import get_data_dir
from .device_presets import DEVICEPreset
from .storage import load_optional


class DMXDevice(BaseModel):
    id: str
    order: int
    channels: int
    active_channels: list[int]
    control_type: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "device_1",
                "order": 1,
                "channels" : 5,
                "active_channels": [1,2],
                "control_type": "manual"
            }
        }
    }
    def get_id(self) -> str:
        return self.id

    def get_active_channels(self) -> list[int]:
        return self.active_channels

    def get_number_channels(self) -> int:
        return self.channels

    @staticmethod
    def load_presets(filepath: str) -> list[DEVICEPreset]:
        return load_optional(filepath, DEVICEPreset)

    def set_active_channels(self, wanted_preset: str, presets: list[DEVICEPreset] | None = None) -> None:
        default_presets_path = str(get_data_dir() / "device_presets.json")
        saved_presets = presets if presets is not None else self.load_presets(default_presets_path)
        for device_preset in saved_presets:
            if device_preset.get_device() == self.id and device_preset.get_id() == wanted_preset:
                self.active_channels = device_preset.channel_values
                return
        self.active_channels = [0] * self.channels
        