#backend/models/scene.py
"""Model for scene"""
from pydantic import BaseModel

from backend.models.dmx_setting import DMXSetting
from backend.models.ledfx_setting import LEDFXSetting


class Scene(BaseModel):
    id: str
    dmx_setting: str
    ledfx_setting: str

    model_config = {
        "json_schema_extra":{
        "example": {
            "id": "scene_1",
            "dmx_setting": "dmx_setting_1",
            "ledfx_setting": "ledfx_setting_1"
            }
        }
    }