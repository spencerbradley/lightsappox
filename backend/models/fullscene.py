"""Full scene: combined DMX/LedFx scene plus optional ILDA scene."""
from pydantic import BaseModel


class FullScene(BaseModel):
    id: str
    scene_id: str
    ilda_scene_id: str = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "full_scene_1",
                "scene_id": "scene_1",
                "ilda_scene_id": "ilda_scene_1",
            }
        }
    }

    def get_id(self) -> str:
        return self.id
