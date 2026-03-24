#backend/models/device_presets.py
"""DMX Presets Page"""
from pydantic import BaseModel

class DEVICEPreset(BaseModel):
    id: str
    channel_values: list[int]
    device: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "scene_1",
                "channel_values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "device": "device_1",
            }
        }
    }

    def get_channel_values(self) -> list[int]:
        return self.channel_values

    def get_device(self) -> str:
        return self.device

    def get_id(self) -> str:
        return self.id

    def set_channel_values(self, channel_values: list[int]) -> None:
        self.channel_values = channel_values

    def set_device(self, device: str) -> None:
        self.device = device

    def set_id(self, id: str) -> None:
        self.id = id