"""Audio feature extraction for AI mode - extracts frequency bands, beat features, spectral centroid, and energy."""
import numpy as np
from typing import Optional


def extract_frequency_bands(fft_data: list[float], sample_rate: float = 44100, fft_size: int = 2048) -> list[float]:
    """
    Extract frequency bands from FFT data.
    
    Returns 5 bands: [bass, low_mid, mid, high_mid, treble]
    - Bass: 20-250 Hz
    - Low-mid: 250-500 Hz
    - Mid: 500-2000 Hz
    - High-mid: 2000-4000 Hz
    - Treble: 4000-20000 Hz
    """
    if not fft_data or len(fft_data) == 0:
        return [0.0] * 5
        
    fft_array = np.array(fft_data)
    freqs = np.fft.fftfreq(fft_size, 1.0 / sample_rate)
    freqs = np.abs(freqs[:len(fft_array)])
    
    # Frequency band ranges (Hz)
    bands = [
        (20, 250),      # Bass
        (250, 500),     # Low-mid
        (500, 2000),    # Mid
        (2000, 4000),   # High-mid
        (4000, 20000),  # Treble
    ]
    
    band_values = []
    for low, high in bands:
        mask = (freqs >= low) & (freqs <= high)
        if np.any(mask):
            band_energy = np.mean(fft_array[mask])
        else:
            band_energy = 0.0
        # Normalize to 0-1 range (assuming input is 0-255)
        band_values.append(float(band_energy / 255.0))
        
    return band_values


def extract_spectral_centroid(fft_data: list[float], sample_rate: float = 44100, fft_size: int = 2048) -> float:
    """
    Calculate spectral centroid (brightness indicator).
    
    Returns normalized value 0-1.
    """
    if not fft_data or len(fft_data) == 0:
        return 0.0
        
    fft_array = np.array(fft_data)
    freqs = np.fft.fftfreq(fft_size, 1.0 / sample_rate)
    freqs = np.abs(freqs[:len(fft_array)])
    
    # Calculate weighted average frequency
    magnitude = fft_array.astype(float)
    if np.sum(magnitude) == 0:
        return 0.0
        
    centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
    
    # Normalize to 0-1 (assuming max frequency is sample_rate/2)
    normalized = centroid / (sample_rate / 2.0)
    return float(np.clip(normalized, 0.0, 1.0))


def extract_energy(fft_data: list[float]) -> float:
    """
    Calculate overall energy/volume level.
    
    Returns normalized value 0-1.
    """
    if not fft_data or len(fft_data) == 0:
        return 0.0
        
    fft_array = np.array(fft_data)
    energy = np.mean(fft_array)
    
    # Normalize to 0-1 (assuming input is 0-255)
    return float(np.clip(energy / 255.0, 0.0, 1.0))


def extract_beat_features(fft_data: list[float], previous_fft: Optional[list[float]] = None,
                         time_since_last_beat: Optional[float] = None) -> list[float]:
    """
    Extract beat-related features.
    
    Returns [tempo_estimate, beat_strength, time_since_last_beat]
    - tempo_estimate: Estimated BPM (normalized 0-1, assuming max 200 BPM)
    - beat_strength: Strength of current beat (0-1)
    - time_since_last_beat: Seconds since last beat (normalized, assuming max 2 seconds)
    """
    if not fft_data or len(fft_data) == 0:
        return [0.0, 0.0, 1.0]  # Default: no tempo, no beat, max time since beat
        
    fft_array = np.array(fft_data)
    
    # Beat strength: focus on bass frequencies (first ~6 bins for 2048 FFT at 44.1kHz)
    bass_bins = min(6, len(fft_array))
    bass_energy = np.mean(fft_array[:bass_bins]) if bass_bins > 0 else 0.0
    
    # Calculate spectral flux for beat detection
    beat_strength = 0.0
    if previous_fft is not None and len(previous_fft) == len(fft_array):
        prev_array = np.array(previous_fft)
        # Spectral flux: sum of positive differences
        diff = fft_array - prev_array
        flux = np.sum(np.maximum(diff, 0))
        beat_strength = float(np.clip(flux / (255.0 * len(fft_array)), 0.0, 1.0))
    else:
        # Use bass energy as proxy if no previous frame
        beat_strength = float(np.clip(bass_energy / 255.0, 0.0, 1.0))
    
    # Tempo estimate: simple heuristic based on energy variation
    # Higher variation suggests faster tempo
    energy_variance = float(np.var(fft_array))
    tempo_estimate = float(np.clip(energy_variance / (255.0 * 255.0), 0.0, 1.0))
    
    # Time since last beat (normalize to 0-1, assuming max 2 seconds)
    if time_since_last_beat is None:
        time_since_last_beat = 2.0  # Default to max
    normalized_time = float(np.clip(time_since_last_beat / 2.0, 0.0, 1.0))
    
    return [tempo_estimate, beat_strength, normalized_time]


def extract_all_features(fft_data: list[float], previous_fft: Optional[list[float]] = None,
                         time_since_last_beat: Optional[float] = None,
                         sample_rate: float = 44100, fft_size: int = 2048) -> list[float]:
    """
    Extract all audio features for AI mode observation.
    
    Returns 10 values:
    - Frequency bands (5): [bass, low_mid, mid, high_mid, treble]
    - Beat features (3): [tempo_estimate, beat_strength, time_since_last_beat]
    - Spectral centroid (1)
    - Energy (1)
    
    Total: 10 values
    """
    frequency_bands = extract_frequency_bands(fft_data, sample_rate, fft_size)
    beat_features = extract_beat_features(fft_data, previous_fft, time_since_last_beat)
    spectral_centroid = extract_spectral_centroid(fft_data, sample_rate, fft_size)
    energy = extract_energy(fft_data)
    
    return frequency_bands + beat_features + [spectral_centroid, energy]
