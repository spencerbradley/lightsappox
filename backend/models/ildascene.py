"""ILDA scene: ordered frame ids with beat or time playback."""
from pydantic import BaseModel, Field


class IldaScene(BaseModel):
    id: str
    ilda_frames: list[str] = Field(default_factory=list)
    beat_synced: bool = True
    time_step: float = 0.1
    """Point scan rate for streaming a frame (ILDA has no per-point timestamps in format 5)."""
    points_per_second: float = 30_000.0
    """Scales stream rate and dwell (higher = faster)."""
    animation_speed: float = 1.0
    """Extra hold after each frame finishes streaming."""
    dwell_seconds: float = 0.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "ilda_scene_1",
                "ilda_frames": ["ildaframe_1", "ildaframe_2"],
                "beat_synced": True,
                "time_step": 0.1,
                "points_per_second": 30000.0,
                "animation_speed": 1.0,
                "dwell_seconds": 0.0,
            }
        }
    }

    def get_id(self) -> str:
        return self.id
