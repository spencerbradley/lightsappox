/**
 * AI Mode page: Reinforcement learning lighting control.
 * Extracts audio features and sends to AI model for prediction.
 */
(function () {
  "use strict";

  // UI Elements
  const toggleBtn = document.getElementById("ai-mode-toggle");
  const toggleText = document.getElementById("toggle-text");
  const statusEl = document.getElementById("ai-mode-status");
  const ratingSlider = document.getElementById("rating-slider");
  const ratingValue = document.getElementById("rating-value");
  const feedbackText = document.getElementById("feedback-text");
  const submitFeedbackBtn = document.getElementById("submit-feedback");
  const undoBtn = document.getElementById("undo-button");
  const presetButtons = document.querySelectorAll(".preset-button");
  const modelStatusEl = document.getElementById("model-status");
  const feedbackCountEl = document.getElementById("feedback-count");
  const preTrainedEl = document.getElementById("pre-trained-status");

  // Audio analysis (reuses code from home.js)
  let stream = null;
  let audioContext = null;
  let analyser = null;
  let rafId = null;
  let dataArray = null;
  let prevSpectrum = null;
  let lastBeatTime = null;

  // AI Mode state
  let aiModeActive = false;
  let predictionInterval = null;
  let lastPredictionTime = 0;
  const MIN_PREDICTION_INTERVAL = 100; // 100ms minimum
  const MAX_PREDICTION_INTERVAL = 500; // 500ms maximum
  const ENERGY_THRESHOLD = 0.3; // Threshold for high energy

  // Audio feature extraction
  function extractFrequencyBands(fftData, sampleRate = 44100, fftSize = 2048) {
    const freqs = [];
    for (let i = 0; i < fftSize / 2; i++) {
      freqs.push((i * sampleRate) / fftSize);
    }

    const bands = [
      { low: 20, high: 250 },      // Bass
      { low: 250, high: 500 },     // Low-mid
      { low: 500, high: 2000 },    // Mid
      { low: 2000, high: 4000 },   // High-mid
      { low: 4000, high: 20000 },  // Treble
    ];

    const bandValues = [];
    for (const band of bands) {
      let sum = 0;
      let count = 0;
      for (let i = 0; i < freqs.length && i < fftData.length; i++) {
        if (freqs[i] >= band.low && freqs[i] <= band.high) {
          sum += fftData[i];
          count++;
        }
      }
      const avg = count > 0 ? sum / count / 255.0 : 0.0;
      bandValues.push(Math.min(1.0, Math.max(0.0, avg)));
    }
    return bandValues;
  }

  function extractSpectralCentroid(fftData, sampleRate = 44100, fftSize = 2048) {
    if (!fftData || fftData.length === 0) return 0.0;

    const freqs = [];
    for (let i = 0; i < fftSize / 2; i++) {
      freqs.push((i * sampleRate) / fftSize);
    }

    let weightedSum = 0;
    let magnitudeSum = 0;

    for (let i = 0; i < Math.min(fftData.length, freqs.length); i++) {
      const magnitude = fftData[i] / 255.0;
      weightedSum += freqs[i] * magnitude;
      magnitudeSum += magnitude;
    }

    if (magnitudeSum === 0) return 0.0;
    const centroid = weightedSum / magnitudeSum;
    const normalized = centroid / (sampleRate / 2.0);
    return Math.min(1.0, Math.max(0.0, normalized));
  }

  function extractEnergy(fftData) {
    if (!fftData || fftData.length === 0) return 0.0;
    let sum = 0;
    for (let i = 0; i < fftData.length; i++) {
      sum += fftData[i];
    }
    const avg = sum / fftData.length / 255.0;
    return Math.min(1.0, Math.max(0.0, avg));
  }

  function extractBeatFeatures(fftData, prevFftData, timeSinceLastBeat) {
    if (!fftData || fftData.length === 0) {
      return [0.0, 0.0, 1.0];
    }

    // Beat strength: focus on bass frequencies (first ~6 bins)
    const bassBins = Math.min(6, fftData.length);
    let bassEnergy = 0;
    for (let i = 0; i < bassBins; i++) {
      bassEnergy += fftData[i];
    }
    bassEnergy = bassEnergy / bassBins / 255.0;

    // Spectral flux for beat detection
    let beatStrength = 0.0;
    if (prevFftData && prevFftData.length === fftData.length) {
      let flux = 0;
      for (let i = 0; i < fftData.length; i++) {
        const diff = fftData[i] - prevFftData[i];
        if (diff > 0) flux += diff;
      }
      beatStrength = Math.min(1.0, flux / (255.0 * fftData.length));
    } else {
      beatStrength = Math.min(1.0, bassEnergy);
    }

    // Tempo estimate: variance-based heuristic
    let variance = 0;
    const mean = extractEnergy(fftData);
    for (let i = 0; i < fftData.length; i++) {
      const diff = (fftData[i] / 255.0) - mean;
      variance += diff * diff;
    }
    variance = variance / fftData.length;
    const tempoEstimate = Math.min(1.0, variance);

    // Time since last beat (normalized, max 2 seconds)
    const normalizedTime = Math.min(1.0, (timeSinceLastBeat || 2.0) / 2.0);

    return [tempoEstimate, beatStrength, normalizedTime];
  }

  function extractAllAudioFeatures(fftData, prevFftData, timeSinceLastBeat) {
    const frequencyBands = extractFrequencyBands(fftData);
    const beatFeatures = extractBeatFeatures(fftData, prevFftData, timeSinceLastBeat);
    const spectralCentroid = extractSpectralCentroid(fftData);
    const energy = extractEnergy(fftData);

    return {
      frequency_bands: frequencyBands,
      beat_features: beatFeatures,
      spectral_centroid: spectralCentroid,
      energy: energy,
    };
  }

  // Adaptive prediction frequency based on energy
  function getPredictionInterval(energy) {
    if (energy > ENERGY_THRESHOLD) {
      // High energy: faster updates
      return MIN_PREDICTION_INTERVAL;
    } else {
      // Low energy: slower updates
      return MAX_PREDICTION_INTERVAL;
    }
  }

  // Send prediction request
  function sendPrediction(audioFeatures) {
    if (!aiModeActive) return;

    const now = Date.now();
    const energy = audioFeatures.energy;
    const interval = getPredictionInterval(energy);

    // Check if enough time has passed
    if (now - lastPredictionTime < interval) {
      return;
    }

    lastPredictionTime = now;

    API.post("/ai-mode/predict", audioFeatures)
      .then(function (response) {
        console.log("[AI Mode] Prediction applied:", response);
      })
      .catch(function (err) {
        console.error("[AI Mode] Prediction failed:", err);
        if (err.message && err.message.includes("404")) {
          // AI mode disabled or not available
          stopAIMode();
          updateStatus("AI mode not available. Check config.json");
        }
      });
  }

  // Audio update loop
  function updateAudioLoop() {
    if (!analyser || !dataArray || !aiModeActive) {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      return;
    }

    analyser.getByteFrequencyData(dataArray);

    // Extract audio features
    const now = performance.now();
    const timeSinceLastBeat = lastBeatTime ? (now - lastBeatTime) / 1000.0 : null;
    const audioFeatures = extractAllAudioFeatures(dataArray, prevSpectrum, timeSinceLastBeat);

    // Update previous spectrum
    if (!prevSpectrum) {
      prevSpectrum = new Uint8Array(dataArray.length);
    }
    for (let i = 0; i < dataArray.length; i++) {
      prevSpectrum[i] = dataArray[i];
    }

    // Send prediction if AI mode is active
    if (aiModeActive) {
      sendPrediction(audioFeatures);
    }

    rafId = requestAnimationFrame(updateAudioLoop);
  }

  // Start AI mode
  function startAIMode() {
    API.post("/ai-mode/start")
      .then(function (response) {
        console.log("[AI Mode] Started:", response);
        aiModeActive = true;
        updateUI();
        startAudioCapture();
        updateStatus("AI Mode is active");
      })
      .catch(function (err) {
        console.error("[AI Mode] Start failed:", err);
        updateStatus("Failed to start: " + (err.message || "unknown error"));
      });
  }

  // Stop AI mode
  function stopAIMode() {
    API.post("/ai-mode/stop")
      .then(function (response) {
        console.log("[AI Mode] Stopped:", response);
        aiModeActive = false;
        updateUI();
        stopAudioCapture();
        updateStatus("AI Mode is inactive");
      })
      .catch(function (err) {
        console.error("[AI Mode] Stop failed:", err);
        updateStatus("Failed to stop: " + (err.message || "unknown error"));
      });
  }

  // Audio capture (reuses logic from home.js)
  function startAudioCapture() {
    const micSelect = document.getElementById("mic-select");
    if (!micSelect) return;

    const deviceId = micSelect.value;
    if (!deviceId) {
      stopAudioCapture();
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      updateStatus("Microphone API not supported");
      return;
    }

    if (stream) {
      stopAudioCapture();
    }

    const constraints = { audio: { deviceId: { exact: deviceId } } };
    navigator.mediaDevices
      .getUserMedia(constraints)
      .then(function (s) {
        stream = s;
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.2;
        source.connect(analyser);
        dataArray = new Uint8Array(analyser.frequencyBinCount);
        prevSpectrum = null;
        lastBeatTime = null;
        updateAudioLoop();
      })
      .catch(function (err) {
        updateStatus("Audio error: " + (err.message || "unknown"));
        stopAudioCapture();
      });
  }

  function stopAudioCapture() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    if (stream) {
      stream.getTracks().forEach(function (t) {
        t.stop();
      });
      stream = null;
    }
    if (audioContext && audioContext.state !== "closed") {
      audioContext.close();
    }
    audioContext = null;
    analyser = null;
    prevSpectrum = null;
    dataArray = null;
  }

  // Submit feedback
  function submitFeedback() {
    if (!aiModeActive) {
      updateStatus("AI mode must be active to submit feedback");
      return;
    }

    const rating = ratingSlider ? parseFloat(ratingSlider.value) : null;
    const text = feedbackText ? feedbackText.value.trim() : null;

    if (!rating && !text) {
      updateStatus("Please provide rating or text feedback");
      return;
    }

    API.post("/ai-mode/feedback", {
      rating: rating,
      text: text || null,
      preset_button: null, // Preset buttons handled separately
    })
      .then(function (response) {
        console.log("[AI Mode] Feedback submitted:", response);
        updateStatus("Feedback submitted successfully");
        // Clear text input
        if (feedbackText) feedbackText.value = "";
        // Refresh status
        refreshStatus();
      })
      .catch(function (err) {
        console.error("[AI Mode] Feedback failed:", err);
        updateStatus("Failed to submit feedback: " + (err.message || "unknown error"));
      });
  }

  // Handle preset button
  function handlePresetButton(presetName) {
    if (!aiModeActive) {
      updateStatus("AI mode must be active");
      return;
    }

    API.post("/ai-mode/feedback", {
      rating: null,
      text: null,
      preset_button: presetName,
    })
      .then(function (response) {
        console.log("[AI Mode] Preset button pressed:", response);
        updateStatus("Behavior modifier applied: " + presetName);
      })
      .catch(function (err) {
        console.error("[AI Mode] Preset button failed:", err);
        updateStatus("Failed: " + (err.message || "unknown error"));
      });
  }

  // Undo last action
  function undoLastAction() {
    if (!aiModeActive) {
      updateStatus("AI mode must be active");
      return;
    }

    API.post("/ai-mode/undo")
      .then(function (response) {
        console.log("[AI Mode] Undo:", response);
        if (response.undone) {
          updateStatus("Last action undone");
        } else {
          updateStatus("No action to undo");
        }
      })
      .catch(function (err) {
        console.error("[AI Mode] Undo failed:", err);
        updateStatus("Failed to undo: " + (err.message || "unknown error"));
      });
  }

  // Update UI
  function updateUI() {
    if (toggleBtn && toggleText) {
      if (aiModeActive) {
        toggleBtn.textContent = "Stop AI Mode";
        toggleBtn.classList.remove("button-primary");
        toggleBtn.classList.add("button-danger");
      } else {
        toggleText.textContent = "Start AI Mode";
        toggleBtn.classList.remove("button-danger");
        toggleBtn.classList.add("button-primary");
      }
    }
  }

  function updateStatus(message) {
    if (statusEl) {
      statusEl.textContent = message;
    }
  }

  // Refresh status display
  function refreshStatus() {
    API.get("/ai-mode/status")
      .then(function (status) {
        aiModeActive = status.active;
        updateUI();

        if (modelStatusEl) {
          modelStatusEl.textContent = status.model_loaded ? "Loaded" : "Not loaded";
        }
        if (feedbackCountEl) {
          feedbackCountEl.textContent = status.feedback_count || 0;
        }
        if (preTrainedEl) {
          preTrainedEl.textContent = status.pre_trained ? "Yes" : "No";
        }

        if (status.active) {
          updateStatus("AI Mode is active");
        } else {
          updateStatus("AI Mode is inactive");
        }
      })
      .catch(function (err) {
        console.error("[AI Mode] Status check failed:", err);
        if (err.message && err.message.includes("404")) {
          updateStatus("AI mode not available. Set ai_mode_enabled=true in config.json");
        }
      });
  }

  // Event listeners
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      if (aiModeActive) {
        stopAIMode();
      } else {
        startAIMode();
      }
    });
  }

  if (ratingSlider && ratingValue) {
    ratingSlider.addEventListener("input", function () {
      ratingValue.textContent = ratingSlider.value;
    });
  }

  if (submitFeedbackBtn) {
    submitFeedbackBtn.addEventListener("click", submitFeedback);
  }

  if (undoBtn) {
    undoBtn.addEventListener("click", undoLastAction);
  }

  presetButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const presetName = btn.getAttribute("data-preset");
      if (presetName) {
        handlePresetButton(presetName);
      }
    });
  });

  // Initialize: check status and set up audio
  document.addEventListener("DOMContentLoaded", function () {
    refreshStatus();

    // Set up audio capture when mic is selected (reuses home.js logic)
    const micSelect = document.getElementById("mic-select");
    if (micSelect) {
      micSelect.addEventListener("change", function () {
        if (aiModeActive) {
          startAudioCapture();
        }
      });
    }
  });
})();
