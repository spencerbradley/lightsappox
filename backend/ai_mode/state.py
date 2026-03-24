"""AI mode state management - tracks active/inactive state, action history, and feedback queue."""
import time
from typing import Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class ActionRecord:
    """Record of an action taken by the AI."""
    timestamp: float
    dmx_values: list[int]
    ledfx_scene: Optional[str]
    audio_features: list[float]


@dataclass
class FeedbackRecord:
    """Record of user feedback."""
    timestamp: float
    rating: Optional[float]  # 1-10 scale
    text: Optional[str]
    preset_button: Optional[str]  # e.g., "More Calm", "Faster"
    action_timestamp: float  # Timestamp of the action this feedback applies to


class AIModeState:
    """Manages AI mode state: active/inactive, action history, feedback queue."""
    
    def __init__(self):
        self._active: bool = False
        self._action_history: deque[ActionRecord] = deque(maxlen=1000)  # Keep last 1000 actions
        self._feedback_queue: deque[FeedbackRecord] = deque(maxlen=500)  # Keep last 500 feedbacks
        self._last_action: Optional[ActionRecord] = None
        
    def is_active(self) -> bool:
        """Check if AI mode is currently active."""
        return self._active
        
    def set_active(self, active: bool) -> None:
        """Set AI mode active/inactive state."""
        self._active = active
        if not active:
            # Clear history when deactivating
            self._action_history.clear()
            self._feedback_queue.clear()
            self._last_action = None
            
    def record_action(self, dmx_values: list[int], ledfx_scene: Optional[str], audio_features: list[float]) -> None:
        """Record an action taken by the AI."""
        record = ActionRecord(
            timestamp=time.time(),
            dmx_values=dmx_values.copy(),
            ledfx_scene=ledfx_scene,
            audio_features=audio_features.copy()
        )
        self._action_history.append(record)
        self._last_action = record
        
    def get_last_action(self) -> Optional[ActionRecord]:
        """Get the most recent action."""
        return self._last_action
        
    def get_recent_actions(self, seconds: float = 2.0) -> list[ActionRecord]:
        """Get actions from the last N seconds."""
        now = time.time()
        cutoff = now - seconds
        return [a for a in self._action_history if a.timestamp >= cutoff]
        
    def add_feedback(self, rating: Optional[float] = None, text: Optional[str] = None, 
                     preset_button: Optional[str] = None, action_timestamp: Optional[float] = None) -> None:
        """Add user feedback to the queue."""
        if action_timestamp is None and self._last_action:
            action_timestamp = self._last_action.timestamp
            
        feedback = FeedbackRecord(
            timestamp=time.time(),
            rating=rating,
            text=text,
            preset_button=preset_button,
            action_timestamp=action_timestamp or time.time()
        )
        self._feedback_queue.append(feedback)
        
    def get_pending_feedback(self) -> list[FeedbackRecord]:
        """Get all pending feedback records."""
        return list(self._feedback_queue)
        
    def clear_feedback(self) -> None:
        """Clear the feedback queue."""
        self._feedback_queue.clear()
        
    def undo_last_action(self) -> Optional[ActionRecord]:
        """Undo the last action (remove it from history)."""
        if self._action_history:
            removed = self._action_history.pop()
            self._last_action = self._action_history[-1] if self._action_history else None
            return removed
        return None


# Global state instance
_state = AIModeState()


def get_state() -> AIModeState:
    """Get the global AI mode state instance."""
    return _state
