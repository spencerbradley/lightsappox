(function () {
  "use strict";

  const micSelect = document.getElementById("mic-select");
  const micStatus = document.getElementById("mic-status");
  const meterBar = document.getElementById("meter-bar");
  const changeIndicator = document.getElementById("change-indicator");

  let stream = null;
  let audioContext = null;
  let analyser = null;
  let rafId = null;
  let dataArray = null;

  // Change detection (spectral flux onset, like old audio.js)
  const FLUX_HISTORY_SIZE = 30;
  const COOLDOWN_MS = 80;
  const SENSITIVITY = 25;  /* Higher = more sensitive (1–100) */
  const MIN_RISE = 18;     /* Flux must jump by this much in one frame (filters slow drift) */
  const DIP_RATIO = 0.62;  /* Previous flux must be below threshold * this (rising edge only) */
  let prevSpectrum = null;
  let fluxHistory = [];
  let lastFlux = 0;
  let lastChangeTime = 0;
  let changeIndicatorTimeout = null;

  function setStatus(text) {
    if (micStatus) micStatus.textContent = text;
  }

  function populateMics(devices) {
    if (!micSelect) return;
    const inputs = devices.filter(function (d) { return d.kind === "audioinput"; });
    micSelect.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "— Select a device —";
    micSelect.appendChild(opt);
    inputs.forEach(function (d) {
      const o = document.createElement("option");
      o.value = d.deviceId;
      o.textContent = d.label || "Microphone " + (micSelect.options.length);
      micSelect.appendChild(o);
    });
    if (inputs.length === 0) {
      setStatus("No microphones found.");
    } else {
      setStatus(inputs.length + " microphone(s) available. Select one to start detection.");
    }
  }

  function stopStream() {
    if (rafId != null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    if (changeIndicatorTimeout) {
      clearTimeout(changeIndicatorTimeout);
      changeIndicatorTimeout = null;
    }
    if (stream) {
      stream.getTracks().forEach(function (t) { t.stop(); });
      stream = null;
    }
    if (audioContext && audioContext.state !== "closed") {
      audioContext.close();
    }
    audioContext = null;
    analyser = null;
    if (meterBar) meterBar.style.width = "0%";
    prevSpectrum = null;
    fluxHistory = [];
    lastFlux = 0;
    lastChangeTime = 0;
    dataArray = null;
    if (changeIndicator) changeIndicator.classList.remove("change-active");
    setStatus("Detection stopped.");
  }

  function getEnergy(data) {
    let sum = 0;
    const len = data.length;
    for (let i = 0; i < len; i++) sum += data[i];
    return len ? sum / len : 0;
  }

  /**
   * Detect change/onset using spectral flux (like old audio.js).
   * Triggers when the spectrum changes sharply in the kick range (roughly 40–200 Hz).
   */
  function detectChange(dataAlreadyFetched) {
    if (!analyser || !dataArray) return;
    const now = performance.now();
    if (now - lastChangeTime < COOLDOWN_MS) return;

    if (!dataAlreadyFetched) analyser.getByteFrequencyData(dataArray);

    if (!prevSpectrum) {
      prevSpectrum = new Uint8Array(dataArray.length);
      for (let j = 0; j < dataArray.length; j++) prevSpectrum[j] = dataArray[j];
      return;
    }

    // Spectral flux in bass-only range (bins 2–6, ~40–100 Hz at 2048 FFT) – weight lowest bins more
    let flux = 0;
    for (let i = 2; i <= 6; i++) {
      const diff = dataArray[i] - prevSpectrum[i];
      if (diff > 0) flux += diff * (1.8 - (i - 2) * 0.2);  /* bin 2 heaviest, 6 lightest */
    }

    for (let j = 0; j < dataArray.length; j++) prevSpectrum[j] = dataArray[j];

    fluxHistory.push(flux);
    if (fluxHistory.length > FLUX_HISTORY_SIZE) fluxHistory.shift();

    if (fluxHistory.length < 8) return;

    let sum = 0;
    for (let k = 0; k < fluxHistory.length; k++) sum += fluxHistory[k];
    const avg = sum / fluxHistory.length;
    let variance = 0;
    for (let m = 0; m < fluxHistory.length; m++) {
      variance += (fluxHistory[m] - avg) * (fluxHistory[m] - avg);
    }
    const stdDev = Math.sqrt(variance / fluxHistory.length);

    const s = Math.max(1, Math.min(100, SENSITIVITY));
    const curve = Math.pow(s / 100, 2.2);
    const multiplier = Math.max(0.5, 2.4 - curve * 2.0);
    const minFlux = 20;  /* Minimum absolute flux - lower allows quieter hits */
    const thresholdMultiplier = 1.22;  /* Higher = less sensitive, need stronger flux to trigger */
    const threshold = (avg + stdDev * multiplier) * thresholdMultiplier;

    /* Require rising edge: previous flux was below baseline, and a minimum jump this frame */
    const wasInDip = lastFlux < threshold * DIP_RATIO;
    const sharpRise = flux - lastFlux >= MIN_RISE;
    lastFlux = flux;

    if (flux > threshold && flux > minFlux && wasInDip && sharpRise) {
      lastChangeTime = now;
      if (changeIndicator) {
        changeIndicator.classList.add("change-active");
        if (changeIndicatorTimeout) clearTimeout(changeIndicatorTimeout);
        changeIndicatorTimeout = setTimeout(function () {
          changeIndicator.classList.remove("change-active");
        }, 80);
      }
      if (window.API) {
        console.log("[Beat] Detected, calling /active-scene/advance");
        API.post("/active-scene/advance")
          .then(function (result) {
            console.log("[Beat] Advance response:", result);
          })
          .catch(function (err) {
            console.error("[Beat] Advance failed:", err);
          });
      } else {
        console.warn("[Beat] API not available");
      }
    }
  }

  function updateMeter() {
    if (!analyser || !dataArray) return;
    analyser.getByteFrequencyData(dataArray);
    if (meterBar) {
      const energy = getEnergy(dataArray);
      const pct = Math.min(100, (energy / 255) * 100);
      meterBar.style.width = pct + "%";
    }
    detectChange(true);
    rafId = requestAnimationFrame(updateMeter);
  }

  function startCapture() {
    if (!micSelect) return;
    const deviceId = micSelect.value;
    if (!deviceId) {
      stopStream();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Microphone API not supported.");
      return;
    }
    // Stop existing stream if changing devices
    if (stream) {
      stopStream();
    }
    setStatus("Starting detection…");
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
        fluxHistory = [];
        lastChangeTime = 0;
        setStatus("Detection active.");
        rafId = requestAnimationFrame(updateMeter);
      })
      .catch(function (err) {
        setStatus("Error: " + (err.message || "unknown"));
        stopStream();
      });
  }

  // Auto-request access on page load
  function requestAccess() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Microphone API not supported.");
      return Promise.reject(new Error("Microphone API not supported"));
    }
    setStatus("Requesting access…");
    return navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(function (s) {
        s.getTracks().forEach(function (t) { t.stop(); });
        return navigator.mediaDevices.enumerateDevices();
      })
      .then(populateMics)
      .catch(function (err) {
        setStatus("Access denied or error: " + (err.message || "unknown"));
        throw err;
      });
  }

  // Auto-start when mic is selected, auto-stop when cleared
  if (micSelect) {
    micSelect.addEventListener("change", function () {
      const deviceId = micSelect.value;
      if (deviceId) {
        // Save selected microphone to localStorage
        localStorage.setItem("selectedMicrophone", deviceId);
        startCapture();
      } else {
        localStorage.removeItem("selectedMicrophone");
        stopStream();
      }
    });
  }

  // Request access on page load
  if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
    if (micSelect) {
      // Page has mic select (home page) - populate dropdown and restore saved selection
      requestAccess()
        .then(function () {
          // After populating mics, try to load saved selection
          const savedMic = localStorage.getItem("selectedMicrophone");
          if (savedMic) {
            // Check if saved mic still exists in the list
            const option = Array.from(micSelect.options).find(function (opt) {
              return opt.value === savedMic;
            });
            if (option) {
              micSelect.value = savedMic;
              startCapture();
            } else {
              localStorage.removeItem("selectedMicrophone");
            }
          }
        })
        .catch(function () {
          // Error already handled in requestAccess
        });
    } else {
      // No mic select (active page) - start only after user tap (avoids suspended AudioContext)
      const savedMic = localStorage.getItem("selectedMicrophone");
      if (savedMic) {
        setStatus("Tap here to start beat detection.");
      } else {
        setStatus("Select a mic on Home, then tap here.");
      }
      function startActivePageAudio() {
        const id = localStorage.getItem("selectedMicrophone");
        if (!id) {
          setStatus("Select a mic on Home first.");
          return;
        }
        if (stream || rafId != null) return; // already running
        setStatus("Starting…");
        navigator.mediaDevices
          .getUserMedia({ audio: { deviceId: { exact: id } } })
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
            fluxHistory = [];
            lastChangeTime = 0;
            setStatus("Beat detection active.");
            if (rafId == null) rafId = requestAnimationFrame(updateMeter);
          })
          .catch(function (err) {
            setStatus("Error: " + (err.message || "unknown"));
            localStorage.removeItem("selectedMicrophone");
          });
      }
      const audioBlock = document.querySelector(".active-page-audio");
      if (audioBlock) {
        audioBlock.addEventListener("click", function () { startActivePageAudio(); }, { once: false });
        audioBlock.style.cursor = "pointer";
        audioBlock.setAttribute("title", "Click to start beat detection");
      }
    }
  } else {
    setStatus("Microphone API not supported.");
  }
})();
