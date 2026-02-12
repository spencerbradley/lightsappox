#backend/models/dmx_presets.py
"""DMX Presets Page"""
from pydantic import BaseModel
from backend.models.device import DMXDevice

class DMXPreset(BaseModel, DMXDevice):
    id: str
    channel_values: list[int] = [] * DMXDevice.get_number_channels()
    device: str = DMXDevice.get_id()

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "scene_1",
                "channel_values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            }
        }
    }

    def get_channel_values(self) -> list[int]:
        return self.channel_values


    def get_device(self) -> str:
        return self.device

    def get_id(self) -> str:
        return self.id