#backend/models/ledfx_setting
"""Ledfx setting page"""

from pydantic import BaseModel

class LEDFXSetting(BaseModel):
    id: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "scene_1",
            }
        }
    }

    def get_ledfx_setting_id(self) -> str:
        return self.id