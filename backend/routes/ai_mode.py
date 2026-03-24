"""AI Mode API routes."""
import numpy as np
from fastapi import APIRouter, HTTPException
from typing import Optional

from routes.data import get_data_dir
from models.ai_mode_state import (
    AIModeStatus,
    FeedbackRequest,
    AudioFeaturesRequest,
    PredictionResponse,
    UndoResponse,
)
from ai_mode.state import get_state
from ai_mode.feedback import calculate_reward, get_behavior_modifier
from ai_mode.audio_features import extract_all_features

router = APIRouter(tags=["ai-mode"])

# Global model manager instance
_model_manager: Optional[object] = None
_model_manager_error: Optional[str] = None


def _get_model_manager():
    """Get or create the model manager instance (lazy import to avoid torch DLL issues at startup)."""
    global _model_manager, _model_manager_error
    
    if _model_manager_error:
        raise HTTPException(
            status_code=503,
            detail=f"AI mode unavailable: {_model_manager_error}. "
                   f"Install Microsoft Visual C++ Redistributable: "
                   f"https://aka.ms/vs/17/release/vc_redist.x64.exe"
        )
    
    if _model_manager is None:
        try:
            from ai_mode.model_manager import ModelManager
            config_path = str(get_data_dir() / "config.json")
            _model_manager = ModelManager(config_path)
            _model_manager.load_model()
        except Exception as e:
            _model_manager_error = str(e)
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize AI model: {e}. "
                       f"Install Microsoft Visual C++ Redistributable: "
                       f"https://aka.ms/vs/17/release/vc_redist.x64.exe"
            )
    return _model_manager


@router.post("/start")
def start_ai_mode():
    """Start AI mode."""
    state = get_state()
    if state.is_active():
        return {"status": "already_active", "message": "AI mode is already active"}
    
    # Initialize model manager and ensure model is loaded
    manager = _get_model_manager()
    
    # Pre-train if not already done
    if not manager.metadata.get("pre_trained", False):
        try:
            manager.pre_train_on_presets()
        except Exception as e:
            print(f"[AI Mode] Pre-training failed: {e}")
    
    # Activate AI mode
    state.set_active(True)
    
    return {"status": "started", "message": "AI mode started successfully"}


@router.post("/stop")
def stop_ai_mode():
    """Stop AI mode."""
    state = get_state()
    if not state.is_active():
        return {"status": "already_stopped", "message": "AI mode is not active"}
    
    # Save model before stopping
    manager = _get_model_manager()
    manager.save_model()
    
    # Deactivate AI mode
    state.set_active(False)
    
    return {"status": "stopped", "message": "AI mode stopped successfully"}


@router.get("/status")
def get_ai_mode_status() -> AIModeStatus:
    """Get current AI mode status."""
    state = get_state()
    manager = _get_model_manager()
    info = manager.get_info()
    
    return AIModeStatus(
        active=state.is_active(),
        model_loaded=info["model_loaded"],
        feedback_count=info["feedback_count"],
        pre_trained=info["metadata"].get("pre_trained", False),
    )


@router.post("/predict", response_model=PredictionResponse)
def predict_action(audio_features: AudioFeaturesRequest):
    """Get AI prediction for given audio features."""
    state = get_state()
    if not state.is_active():
        raise HTTPException(status_code=400, detail="AI mode is not active. Call /start first")
    
    manager = _get_model_manager()
    
    # Combine audio features into observation vector (10 values)
    observation = np.array(
        audio_features.frequency_bands +
        audio_features.beat_features +
        [audio_features.spectral_centroid, audio_features.energy],
        dtype=np.float32
    )
    
    if len(observation) != 10:
        raise HTTPException(status_code=400, detail=f"Expected 10 audio features, got {len(observation)}")
    
    try:
        # Get prediction from model
        action = manager.predict(observation, deterministic=False)
        
        # Apply action through environment
        env = manager.initialize_env()
        env.set_observation(observation.tolist())
        
        # Apply behavior modifier if set
        # (This would be set from previous feedback)
        
        # Step environment to apply action
        obs, reward, terminated, truncated, info = env.step(action)
        
        dmx_values = info.get("dmx_values", [])
        ledfx_scene = info.get("ledfx_scene")
        
        return PredictionResponse(
            dmx_values=dmx_values,
            ledfx_scene=ledfx_scene,
            action_applied=True,
        )
        
    except Exception as e:
        print(f"[AI Mode] Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback."""
    state = get_state()
    if not state.is_active():
        raise HTTPException(status_code=400, detail="AI mode is not active")
    
    # Handle behavior modifier (preset buttons)
    behavior_modifier = None
    if feedback.preset_button:
        behavior_modifier = get_behavior_modifier(feedback.preset_button)
        if behavior_modifier:
            # Set behavior modifier in environment
            manager = _get_model_manager()
            env = manager.initialize_env()
            env.set_behavior_modifier(behavior_modifier)
    
    # Calculate reward from rating/text feedback
    reward = calculate_reward(rating=feedback.rating, text=feedback.text)
    
    # Add feedback to state
    state.add_feedback(
        rating=feedback.rating,
        text=feedback.text,
        preset_button=feedback.preset_button,
    )
    
    # Add feedback to model manager for online learning
    if reward != 0.0:
        manager = _get_model_manager()
        manager.add_feedback(reward)
    
    return {
        "status": "received",
        "reward": reward,
        "behavior_modifier": behavior_modifier,
        "message": "Feedback received successfully",
    }


@router.post("/undo", response_model=UndoResponse)
def undo_last_action():
    """Undo the last AI action."""
    state = get_state()
    if not state.is_active():
        raise HTTPException(status_code=400, detail="AI mode is not active")
    
    # Undo last action
    undone_action = state.undo_last_action()
    
    if undone_action:
        # Reload devices to previous state
        # Note: This is simplified - in production you'd want to restore exact previous state
        from routes.data import load_devices, save_devices
        
        devices = load_devices()
        scene_based_devices = [d for d in devices if (d.control_type or "").lower() != "manual"]
        
        # Restore DMX values from undone action
        channel_idx = 0
        for device in scene_based_devices:
            device_channels = undone_action.dmx_values[channel_idx:channel_idx + device.channels]
            if len(device_channels) == device.channels:
                device.active_channels = device_channels
            channel_idx += device.channels
        
        save_devices(devices)
        
        # Restore LEDFX scene if applicable
        if undone_action.ledfx_scene:
            try:
                manager = _get_model_manager()
                env = manager.initialize_env()
                if env.ledfx_client:
                    env.ledfx_client.set_active_scene(undone_action.ledfx_scene)
            except Exception as e:
                print(f"[AI Mode] Failed to restore LEDFX scene: {e}")
        
        return UndoResponse(
            undone=True,
            previous_action={
                "dmx_values": undone_action.dmx_values,
                "ledfx_scene": undone_action.ledfx_scene,
                "timestamp": undone_action.timestamp,
            }
        )
    else:
        return UndoResponse(undone=False, previous_action=None)
