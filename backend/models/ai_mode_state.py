"""Pydantic models for AI mode API serialization."""
from pydantic import BaseModel
from typing import Optional


class AIModeStatus(BaseModel):
    """Status of AI mode."""
    active: bool
    model_loaded: bool
    feedback_count: int
    pre_trained: bool
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "active": True,
                "model_loaded": True,
                "feedback_count": 42,
                "pre_trained": True,
            }
        }
    }


class FeedbackRequest(BaseModel):
    """User feedback request."""
    rating: Optional[float] = None  # 1-10 scale
    text: Optional[str] = None
    preset_button: Optional[str] = None  # "More Calm", "More Energetic", "Faster", "Slower"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rating": 8.0,
                "text": "more calm",
                "preset_button": None,
            }
        }
    }


class AudioFeaturesRequest(BaseModel):
    """Audio features for prediction."""
    frequency_bands: list[float]  # 5 values: [bass, low_mid, mid, high_mid, treble]
    beat_features: list[float]  # 3 values: [tempo_estimate, beat_strength, time_since_last_beat]
    spectral_centroid: float
    energy: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "frequency_bands": [0.5, 0.3, 0.4, 0.2, 0.1],
                "beat_features": [0.6, 0.8, 0.2],
                "spectral_centroid": 0.4,
                "energy": 0.7,
            }
        }
    }


class PredictionResponse(BaseModel):
    """AI prediction response."""
    dmx_values: list[int]
    ledfx_scene: Optional[str]
    action_applied: bool
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "dmx_values": [128, 64, 192, 0, 255],
                "ledfx_scene": "scene_1",
                "action_applied": True,
            }
        }
    }


class UndoResponse(BaseModel):
    """Response from undo action."""
    undone: bool
    previous_action: Optional[dict] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "undone": True,
                "previous_action": {
                    "dmx_values": [128, 64, 192],
                    "ledfx_scene": "scene_1",
                }
            }
        }
    }
