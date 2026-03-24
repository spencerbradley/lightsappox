/**
 * Active page: scene boxes + manual device sliders.
 * Scene-based devices are controlled by presets/scenes; manual devices get sliders for active channels.
 */
(function () {
  "use strict";

  const container = document.getElementById("scene-boxes");
  const statusEl = document.getElementById("active-status");
  const manualDevicesEl = document.getElementById("manual-devices");

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  /** Manual devices get sliders on Active. Scene-based (gigbar, keobin) are preset/scene only. Haze always gets sliders. */
  function isManualDevice(d) {
    if (!d || !d.id) return false;
    var id = d.id.toLowerCase();
    if (id === "haze") return true;
    var sceneBasedIds = ["gigbar", "keobin"];
    if (sceneBasedIds.indexOf(id) >= 0) return false;
    return (d.control_type || "").toLowerCase() === "manual";
  }

  function renderManualDevices(devices) {
    if (!manualDevicesEl) return;
    var manual = (devices || []).filter(isManualDevice);
    if (manual.length === 0) {
      manualDevicesEl.innerHTML = "";
      return;
    }
    manualDevicesEl.innerHTML = manual
      .map(function (device) {
        var id = device.id || "";
        var channels = device.active_channels || [];
        var chCount = Math.max(device.channels || 0, channels.length);
        while (channels.length < chCount) channels.push(0);
        var sliders = channels
          .map(function (val, idx) {
            var ch = idx + 1;
            var v = val || 0;
            return (
              '<label class="manual-channel">' +
              "<span class=\"manual-channel-num\">" + ch + "</span>" +
              '<input type="range" min="0" max="255" value="' + v + '" data-device="' + id + '" data-channel="' + idx + '" aria-label="Channel ' + ch + '">' +
              '<span class="manual-channel-value">' + v + '</span>' +
              "</label>"
            );
          })
          .join("");
        return (
          '<div class="card manual-device-card" data-device="' + id + '">' +
          "<h2 class=\"section-sub\">" + id + "</h2>" +
          '<div class="manual-device-channels">' + sliders + "</div>" +
          "</div>"
        );
      })
      .join("");

    var putTimeout = {};
    manualDevicesEl.querySelectorAll("input[type=range]").forEach(function (input) {
      function updateValueDisplay() {
        var valEl = input.closest(".manual-channel").querySelector(".manual-channel-value");
        if (valEl) valEl.textContent = input.value;
      }
      updateValueDisplay();
      input.addEventListener("input", function () {
        updateValueDisplay();
        var deviceId = input.getAttribute("data-device");
        var card = manualDevicesEl.querySelector(".manual-device-card[data-device=\"" + deviceId + "\"]");
        if (!card) return;
        var inputs = card.querySelectorAll("input[type=range]");
        var channels = Array.from(inputs).map(function (inp) { return parseInt(inp.value, 10) || 0; });
        clearTimeout(putTimeout[deviceId]);
        putTimeout[deviceId] = setTimeout(function () {
          API.put("/devices/" + encodeURIComponent(deviceId) + "/channels", channels).catch(function (err) {
            console.error("Failed to update channels", err);
          });
        }, 80);
      });
    });
  }

  function applyScene(sceneId) {
    setStatus("Applying…");
    API.post("/apply/scene/" + encodeURIComponent(sceneId))
      .then(function () {
        setStatus("Applied: " + sceneId);
        setActiveIndicator(sceneId);
      })
      .catch(function (err) {
        setStatus("Failed: " + (err.message || "unknown"));
      });
  }

  function setActiveIndicator(activeSceneId) {
    if (!container) return;
    container.querySelectorAll(".scene-box").forEach(function (btn) {
      var id = btn.getAttribute("data-id");
      btn.classList.toggle("active", id === activeSceneId);
    });
  }

  function moveScene(sceneIds, index, direction) {
    var newIndex = index + direction;
    if (newIndex < 0 || newIndex >= sceneIds.length) return;
    var swapped = sceneIds.slice();
    var tmp = swapped[index];
    swapped[index] = swapped[newIndex];
    swapped[newIndex] = tmp;
    API.put("/scenes/reorder", { scene_ids: swapped })
      .then(function () {
        renderScenes();
      })
      .catch(function (err) {
        setStatus("Failed to reorder: " + (err.message || "unknown"));
      });
  }

  function renderScenes() {
    Promise.all([API.get("/scenes"), API.get("/active-scene"), API.get("/devices")])
      .then(function (results) {
        var scenes = results[0];
        var activeState = results[1] || {};
        var devices = results[2] || [];
        var activeSceneId = activeState.scene_id || null;

        renderManualDevices(devices);

        if (!container) return;
        var list = scenes || [];
        if (list.length === 0) {
          container.innerHTML = "";
          setStatus("No scenes saved yet.");
          return;
        }
        setStatus("");
        var sceneIds = list.map(function (s) { return s.id; });
        container.innerHTML = list
          .map(function (s, idx) {
            var activeClass = s.id === activeSceneId ? " active" : "";
            var leftDisabled = idx === 0 ? " disabled" : "";
            var rightDisabled = idx === list.length - 1 ? " disabled" : "";
            return (
              '<div class="scene-box-wrap">' +
              '<button type="button" class="scene-box' + activeClass + '" data-id="' + s.id + '">' +
              '<span class="scene-box-arrow scene-box-arrow-left" data-index="' + idx + '" aria-label="Move left"' + leftDisabled + '>‹</span>' +
              '<span class="scene-box-label">' + (s.id || "") + '</span>' +
              '<span class="scene-box-arrow scene-box-arrow-right" data-index="' + idx + '" aria-label="Move right"' + rightDisabled + '>›</span>' +
              '</button>' +
              '</div>'
            );
          })
          .join("");

        container.querySelectorAll(".scene-box").forEach(function (btn) {
          var id = btn.getAttribute("data-id");
          btn.addEventListener("click", function (e) {
            if (e.target.classList.contains("scene-box-arrow")) return;
            applyScene(id);
          });
        });

        container.querySelectorAll(".scene-box-arrow-left").forEach(function (span) {
          if (span.hasAttribute("disabled")) return;
          span.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var idx = parseInt(span.getAttribute("data-index"), 10);
            moveScene(sceneIds, idx, -1);
          });
        });
        container.querySelectorAll(".scene-box-arrow-right").forEach(function (span) {
          if (span.hasAttribute("disabled")) return;
          span.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var idx = parseInt(span.getAttribute("data-index"), 10);
            moveScene(sceneIds, idx, 1);
          });
        });
      })
      .catch(function (err) {
        if (container) container.innerHTML = "";
        setStatus("Failed to load scenes: " + (err.message || "unknown"));
      });
  }

  document.addEventListener("DOMContentLoaded", renderScenes);
})();
