"""Gymnasium environment for AI mode reinforcement learning."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional, Tuple, Dict, Any
import time

from routes.data import load_devices, save_devices, get_data_dir
from ledfx.client import LEDFXClient
from ai_mode.state import get_state, ActionRecord
from ai_mode.feedback import calculate_reward, apply_reward_decay, get_behavior_modifier


class LightsControlEnv(gym.Env):
    """
    Gymnasium environment for controlling DMX lights and LEDFX scenes via reinforcement learning.
    
    Observation space: 10 values (frequency bands, beat features, spectral centroid, energy)
    Action space: Continuous DMX channel values (0-255) + LEDFX scene index (as float, rounded)
    """
    
    metadata = {"render_modes": []}
    
    def __init__(self, config_filepath: str):
        super().__init__()
        
        self.config_filepath = config_filepath
        self.state = get_state()
        
        # Load devices and LEDFX scenes to determine action space size
        self.devices = load_devices()
        self.scene_based_devices = [d for d in self.devices if (d.control_type or "").lower() != "manual"]
        self.total_dmx_channels = sum(d.channels for d in self.scene_based_devices)
        
        # Load LEDFX scenes
        try:
            self.ledfx_client = LEDFXClient(config_filepath, port=8888)
            ledfx_scenes = self.ledfx_client.get_scenes()
            self.ledfx_scene_ids = list(ledfx_scenes.get("scenes", {}).keys())
            if not self.ledfx_scene_ids:
                self.ledfx_scene_ids = [""]  # Empty scene if none available
        except Exception as e:
            print(f"[AI Env] LEDFX unavailable: {e}")
            self.ledfx_client = None
            self.ledfx_scene_ids = [""]
        
        # Observation space: 10 values (frequency bands, beat features, spectral centroid, energy)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(10,),
            dtype=np.float32
        )
        
        # Action space: DMX channels (0-255) + LEDFX scene index (0 to num_scenes-1, as float)
        # Last value is LEDFX scene index (will be rounded when applying)
        self.action_space = spaces.Box(
            low=0.0,
            high=255.0,
            shape=(self.total_dmx_channels + 1,),  # +1 for LEDFX scene index
            dtype=np.float32
        )
        
        # Behavior modifiers
        self.current_behavior_modifier: Optional[str] = None
        
        # Current observation (audio features)
        self.current_observation: np.ndarray = np.zeros(10, dtype=np.float32)
        
        # Track previous DMX values for smooth transitions
        self.previous_dmx_values: Optional[np.ndarray] = None
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """Reset the environment."""
        super().reset(seed=seed)
        
        # Reload devices in case they changed
        self.devices = load_devices()
        self.scene_based_devices = [d for d in self.devices if (d.control_type or "").lower() != "manual"]
        self.total_dmx_channels = sum(d.channels for d in self.scene_based_devices)
        
        # Reset previous values
        self.previous_dmx_values = None
        
        # Return zero observation (will be updated with real audio features)
        self.current_observation = np.zeros(10, dtype=np.float32)
        
        return self.current_observation.copy(), {}
        
    def set_observation(self, audio_features: list[float]) -> None:
        """Set the current observation (audio features)."""
        if len(audio_features) == 10:
            self.current_observation = np.array(audio_features, dtype=np.float32)
        else:
            print(f"[AI Env] Warning: Expected 10 audio features, got {len(audio_features)}")
            self.current_observation = np.zeros(10, dtype=np.float32)
            
    def set_behavior_modifier(self, modifier: Optional[str]) -> None:
        """Set behavior modifier (calm, energetic, faster, slower)."""
        self.current_behavior_modifier = modifier
        
    def _apply_action(self, action: np.ndarray) -> Tuple[list[int], Optional[str]]:
        """
        Apply action to devices and LEDFX.
        
        Returns: (dmx_values_list, ledfx_scene_id)
        """
        # Split action: DMX channels + LEDFX scene index
        dmx_action = action[:-1]  # All but last
        ledfx_index_float = action[-1]  # Last value
        
        # Clamp DMX values to 0-255 and convert to int
        dmx_values = np.clip(dmx_action, 0.0, 255.0).astype(int).tolist()
        
        # Apply behavior modifiers
        if self.current_behavior_modifier == "calm":
            # Slower, gentler transitions - smooth with previous values
            if self.previous_dmx_values is not None:
                alpha = 0.3  # Blend factor (lower = smoother)
                prev_array = np.array(self.previous_dmx_values)
                curr_array = np.array(dmx_values)
                dmx_values = ((1 - alpha) * prev_array + alpha * curr_array).astype(int).tolist()
        elif self.current_behavior_modifier == "energetic":
            # Faster, more dynamic - amplify changes
            if self.previous_dmx_values is not None:
                prev_array = np.array(self.previous_dmx_values)
                curr_array = np.array(dmx_values)
                diff = curr_array - prev_array
                # Amplify changes by 1.5x
                dmx_values = (prev_array + diff * 1.5).astype(int).tolist()
                dmx_values = np.clip(dmx_values, 0, 255).tolist()
        
        # Round LEDFX scene index and clamp
        ledfx_scene_id = None
        if len(self.ledfx_scene_ids) > 1:  # Only if we have scenes
            ledfx_index = int(np.clip(round(ledfx_index_float), 0, len(self.ledfx_scene_ids) - 1))
            ledfx_scene_id = self.ledfx_scene_ids[ledfx_index]
        elif len(self.ledfx_scene_ids) == 1 and self.ledfx_scene_ids[0]:
            ledfx_scene_id = self.ledfx_scene_ids[0]
        
        # Apply DMX values to devices
        channel_idx = 0
        updated_devices = []
        for device in self.devices:
            if (device.control_type or "").lower() != "manual":
                # This is a scene-based device
                device_channels = dmx_values[channel_idx:channel_idx + device.channels]
                # Pad or truncate to match device channels
                if len(device_channels) < device.channels:
                    device_channels.extend([0] * (device.channels - len(device_channels)))
                elif len(device_channels) > device.channels:
                    device_channels = device_channels[:device.channels]
                    
                device.active_channels = device_channels
                channel_idx += device.channels
            updated_devices.append(device)
        
        # Save devices
        save_devices(updated_devices)
        self.devices = updated_devices
        
        # Apply LEDFX scene
        if ledfx_scene_id and self.ledfx_client:
            try:
                self.ledfx_client.set_active_scene(ledfx_scene_id)
            except Exception as e:
                print(f"[AI Env] Failed to set LEDFX scene {ledfx_scene_id}: {e}")
                ledfx_scene_id = None
        
        # Store previous values for next step
        self.previous_dmx_values = np.array(dmx_values)
        
        return dmx_values, ledfx_scene_id
        
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.
        
        Returns: (observation, reward, terminated, truncated, info)
        """
        # Apply action
        dmx_values, ledfx_scene_id = self._apply_action(action)
        
        # Record action in state
        audio_features = self.current_observation.tolist()
        self.state.record_action(dmx_values, ledfx_scene_id, audio_features)
        
        # Calculate reward from pending feedback
        reward = self._calculate_reward_from_feedback()
        
        # Never terminate (continuous control)
        terminated = False
        truncated = False
        
        info = {
            "dmx_values": dmx_values,
            "ledfx_scene": ledfx_scene_id,
            "behavior_modifier": self.current_behavior_modifier,
        }
        
        return self.current_observation.copy(), reward, terminated, truncated, info
        
    def _calculate_reward_from_feedback(self) -> float:
        """Calculate reward from pending feedback with temporal decay."""
        pending_feedback = self.state.get_pending_feedback()
        if not pending_feedback:
            return 0.0
        
        total_reward = 0.0
        now = time.time()
        
        # Get recent actions (last 2 seconds)
        recent_actions = self.state.get_recent_actions(seconds=2.0)
        
        for feedback in pending_feedback:
            # Calculate reward from this feedback
            reward = calculate_reward(
                rating=feedback.rating,
                text=feedback.text
            )
            
            if reward == 0.0:
                continue
            
            # Find the action this feedback applies to
            action_age = now - feedback.action_timestamp
            
            # Apply decay
            decayed_reward = apply_reward_decay(reward, action_age, decay_half_life=1.0)
            
            # Weight by how recent the action was
            total_reward += decayed_reward
        
        # Clear processed feedback (in real implementation, we'd mark as processed)
        # For now, we'll clear all feedback after processing
        # In production, you might want to keep a history
        
        return float(np.clip(total_reward, -1.0, 1.0))  # Clamp reward
        
    def get_action_space_info(self) -> Dict[str, Any]:
        """Get information about the action space."""
        return {
            "total_dmx_channels": self.total_dmx_channels,
            "num_ledfx_scenes": len(self.ledfx_scene_ids),
            "action_space_size": self.total_dmx_channels + 1,
            "scene_based_devices": [d.id for d in self.scene_based_devices],
        }
