"""ILDA frame catalog entry (.ild file path)."""
from pydantic import BaseModel


class IldaFrame(BaseModel):
    id: str
    path: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "ildaframe_1",
                "path": "path/to/ildaframe_1.ild",
            }
        }
    }

    def get_id(self) -> str:
        return self.id

    def get_path(self) -> str:
        return self.path
