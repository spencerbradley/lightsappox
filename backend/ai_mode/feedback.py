"""Feedback processor - converts user feedback to numeric rewards for reinforcement learning."""
from typing import Optional


# Keyword mappings for text feedback
POSITIVE_KEYWORDS = {
    "good": 1.0,
    "great": 1.0,
    "perfect": 1.0,
    "excellent": 1.0,
    "amazing": 1.0,
    "love": 1.0,
    "yes": 0.8,
    "nice": 0.8,
    "cool": 0.7,
}

NEGATIVE_KEYWORDS = {
    "bad": -1.0,
    "terrible": -1.0,
    "wrong": -1.0,
    "awful": -1.0,
    "hate": -1.0,
    "no": -0.8,
    "stop": -0.8,
    "worse": -0.9,
}

CALM_KEYWORDS = {
    "calm": 0.5,
    "softer": 0.5,
    "gentle": 0.5,
    "smooth": 0.4,
    "relaxed": 0.4,
    "peaceful": 0.5,
    "quiet": 0.4,
}

ENERGETIC_KEYWORDS = {
    "energetic": 0.5,
    "faster": 0.5,
    "intense": 0.5,
    "more": 0.3,
    "louder": 0.4,
    "stronger": 0.4,
    "harder": 0.4,
}

# Preset buttons modify behavior, not direct rewards
BEHAVIOR_MODIFIERS = {
    "More Calm": "calm",      # Encourage slower, gentler changes
    "More Energetic": "energetic",  # Encourage faster, more dynamic changes
    "Faster": "faster",       # Increase rate of changes
    "Slower": "slower",      # Decrease rate of changes
}


def parse_text_feedback(text: str) -> float:
    """
    Parse text feedback and return reward value.
    
    Returns reward in range [-1.0, 1.0] based on keyword matching.
    """
    if not text:
        return 0.0
        
    text_lower = text.lower().strip()
    
    # Check for positive keywords
    for keyword, reward in POSITIVE_KEYWORDS.items():
        if keyword in text_lower:
            return reward
            
    # Check for negative keywords
    for keyword, reward in NEGATIVE_KEYWORDS.items():
        if keyword in text_lower:
            return reward
            
    # Check for calm keywords
    for keyword, reward in CALM_KEYWORDS.items():
        if keyword in text_lower:
            return reward
            
    # Check for energetic keywords
    for keyword, reward in ENERGETIC_KEYWORDS.items():
        if keyword in text_lower:
            return reward
    
    # Default: neutral
    return 0.0


def rating_to_reward(rating: float) -> float:
    """
    Convert rating slider value (1-10) to reward (-1.0 to +1.0).
    
    Linear mapping:
    - 1 → -1.0
    - 5 → 0.0 (neutral)
    - 10 → +1.0
    """
    if rating is None:
        return 0.0
        
    # Clamp to 1-10 range
    rating = max(1.0, min(10.0, float(rating)))
    
    # Linear mapping: (rating - 5) / 5
    # This gives: 1→-0.8, 5→0.0, 10→1.0
    # But we want 1→-1.0, so: (rating - 5.5) / 4.5
    reward = (rating - 5.5) / 4.5
    
    # Clamp to [-1.0, 1.0]
    return max(-1.0, min(1.0, reward))


def get_behavior_modifier(preset_button: str) -> Optional[str]:
    """
    Get behavior modifier from preset button name.
    
    Returns modifier string ("calm", "energetic", "faster", "slower") or None if unknown.
    """
    return BEHAVIOR_MODIFIERS.get(preset_button)


def calculate_reward(rating: Optional[float] = None, text: Optional[str] = None) -> float:
    """
    Calculate reward from user feedback (rating slider and text only).
    
    Preset buttons are handled separately as behavior modifiers, not direct rewards.
    
    Priority:
    1. Rating slider (if provided) - strongest signal
    2. Text feedback (if provided)
    
    If both are provided, uses the one with highest absolute value.
    """
    rewards = []
    
    if rating is not None:
        rewards.append(("rating", rating_to_reward(rating)))
        
    if text:
        rewards.append(("text", parse_text_feedback(text)))
    
    if not rewards:
        return 0.0
    
    # Return the reward with highest absolute value (strongest signal)
    return max(rewards, key=lambda x: abs(x[1]))[1]


def apply_reward_decay(reward: float, action_age_seconds: float, decay_half_life: float = 1.0) -> float:
    """
    Apply temporal decay to reward based on action age.
    
    Args:
        reward: Original reward value
        action_age_seconds: How many seconds ago the action occurred
        decay_half_life: Half-life in seconds (default 1.0 = reward halves every second)
    
    Returns:
        Decayed reward value
    """
    if action_age_seconds <= 0:
        return reward
        
    # Exponential decay: reward * (0.5 ^ (age / half_life))
    decay_factor = 0.5 ** (action_age_seconds / decay_half_life)
    return reward * decay_factor
