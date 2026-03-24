/**
 * Presets page: name + per-device preset dropdowns + LedFx preset.
 * Save/load presets, apply, edit, delete.
 */
(function () {
  "use strict";

  let devices = [];
  let devicePresets = [];
  let ledfxScenes = [];
  let presets = [];
  let editingId = null;

  const form = document.getElementById("preset-form");
  const formTitle = document.getElementById("preset-form-title");
  const nameInput = document.getElementById("preset-name");
  const deviceFieldsRoot = document.getElementById("device-presets-fields");
  const ledfxSelect = document.getElementById("ledfx-preset");
  const cancelBtn = document.getElementById("btn-cancel-edit");
  const presetListEl = document.getElementById("preset-list");
  const statusEl = document.getElementById("presets-status");

  function slugify(str) {
    return str
      .toLowerCase()
      .trim()
      .replace(/\s+/g, "_")
      .replace(/[^a-z0-9_]/g, "");
  }

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  /** Only scene-based devices appear on the presets page; manual devices (e.g. haze) are excluded. */
  function isSceneBased(device) {
    return (device.control_type || "").toLowerCase() !== "manual";
  }

  function getSceneBasedDevices() {
    return (devices || []).filter(isSceneBased);
  }

  function presetsForDevice(deviceId) {
    return devicePresets.filter(function (p) {
      return p.device === deviceId;
    });
  }

  function getLedfxSceneIds(data) {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (data.scenes && typeof data.scenes === "object") {
      return Object.keys(data.scenes);
    }
    return [];
  }

  function loadData() {
    Promise.allSettled([
      API.get("/devices"),
      API.get("/device-presets"),
      API.get("/presets"),
      API.get("/ledfx/scenes").catch(function () {
        return { scenes: {} };
      })
    ])
      .then(function (outcomes) {
        devices = outcomes[0].status === "fulfilled" ? (outcomes[0].value || []) : [];
        devicePresets = outcomes[1].status === "fulfilled" ? (outcomes[1].value || []) : [];
        presets = outcomes[2].status === "fulfilled" ? (outcomes[2].value || []) : [];
        var ledfxData = outcomes[3].status === "fulfilled" ? outcomes[3].value : { scenes: {} };
        ledfxScenes = getLedfxSceneIds(ledfxData);

        var errors = [];
        if (outcomes[0].status === "rejected") errors.push("devices: " + (outcomes[0].reason && outcomes[0].reason.message));
        if (outcomes[1].status === "rejected") errors.push("device-presets: " + (outcomes[1].reason && outcomes[1].reason.message));
        if (outcomes[2].status === "rejected") errors.push("presets: " + (outcomes[2].reason && outcomes[2].reason.message));
        if (errors.length) {
          setStatus("Partial load: " + errors.join("; "));
          console.error("Presets page load errors:", outcomes);
        } else {
          setStatus("");
        }

        renderDeviceFields();
        renderLedfxSelect();
        renderPresetList();
      })
      .catch(function (err) {
        setStatus("Failed to load: " + (err.message || "unknown"));
        console.error(err);
      });
  }

  function renderDeviceFields() {
    if (!deviceFieldsRoot) return;
    deviceFieldsRoot.innerHTML = "";
    getSceneBasedDevices().forEach(function (device) {
      var presetsForDev = presetsForDevice(device.id);
      var wrap = document.createElement("div");
      wrap.className = "form-group";
      var label = document.createElement("label");
      label.setAttribute("for", "device-preset-" + device.id);
      label.textContent = device.id;
      var select = document.createElement("select");
      select.id = "device-preset-" + device.id;
      select.setAttribute("data-device", device.id);
      select.setAttribute("aria-label", "Preset for " + device.id);
      var opt0 = document.createElement("option");
      opt0.value = "";
      opt0.textContent = "— None —";
      select.appendChild(opt0);
      presetsForDev.forEach(function (p) {
        var opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.id;
        select.appendChild(opt);
      });
      wrap.appendChild(label);
      wrap.appendChild(select);
      deviceFieldsRoot.appendChild(wrap);
    });
  }

  function renderLedfxSelect() {
    if (!ledfxSelect) return;
    var first = ledfxSelect.querySelector("option");
    ledfxSelect.innerHTML = "";
    if (first) ledfxSelect.appendChild(first);
    else {
      var none = document.createElement("option");
      none.value = "";
      none.textContent = "— None —";
      ledfxSelect.appendChild(none);
    }
    ledfxScenes.forEach(function (id) {
      var opt = document.createElement("option");
      opt.value = id;
      opt.textContent = id;
      ledfxSelect.appendChild(opt);
    });
  }

  function getFormPayload() {
    var name = (nameInput && nameInput.value.trim()) || "";
    var id = editingId !== null ? editingId : slugify(name);
    var devicePresetIds = [];
    getSceneBasedDevices().forEach(function (device) {
      var sel = document.getElementById("device-preset-" + device.id);
      if (sel && sel.value) devicePresetIds.push(sel.value);
    });
    var ledfx = ledfxSelect && ledfxSelect.value ? ledfxSelect.value : "";
    return {
      id: id,
      device_presets: devicePresetIds,
      ledfx_setting: ledfx
    };
  }

  function setFormFromPreset(preset) {
    if (nameInput) nameInput.value = preset.id || "";
    var ids = preset.device_presets || [];
    getSceneBasedDevices().forEach(function (device, index) {
      var sel = document.getElementById("device-preset-" + device.id);
      if (!sel) return;
      sel.value = (ids[index] && String(ids[index]).trim()) || "";
    });
    if (ledfxSelect) ledfxSelect.value = preset.ledfx_setting || "";
  }

  function clearForm() {
    editingId = null;
    if (formTitle) formTitle.textContent = "New preset";
    if (nameInput) nameInput.value = "";
    getSceneBasedDevices().forEach(function (device) {
      var sel = document.getElementById("device-preset-" + device.id);
      if (sel) sel.value = "";
    });
    if (ledfxSelect) ledfxSelect.value = "";
    if (cancelBtn) cancelBtn.style.display = "none";
  }

  function renderPresetList() {
    if (!presetListEl) return;
    if (presets.length === 0) {
      presetListEl.innerHTML = "";
      if (!statusEl || !statusEl.textContent) setStatus("No presets saved yet.");
      return;
    }
    if (statusEl && statusEl.textContent.indexOf("Partial") === -1) setStatus("");
    presetListEl.innerHTML = presets
      .map(function (p) {
        return (
          '<div class="scene-item" data-id="' +
          p.id +
          '">' +
          "<span>" +
          p.id +
          "</span>" +
          "<div>" +
          '<button type="button" class="btn btn-small btn-primary" data-action="apply" data-id="' +
          p.id +
          '">Apply</button>' +
          '<button type="button" class="btn btn-small btn-secondary" data-action="edit" data-id="' +
          p.id +
          '">Edit</button>' +
          '<button type="button" class="btn btn-small btn-danger" data-action="delete" data-id="' +
          p.id +
          '">Delete</button>' +
          "</div>" +
          "</div>"
        );
      })
      .join("");

    presetListEl.querySelectorAll("[data-action]").forEach(function (btn) {
      var action = btn.getAttribute("data-action");
      var id = btn.getAttribute("data-id");
      btn.onclick = function (e) {
        e.stopPropagation();
        if (action === "apply") applyPreset(id);
        else if (action === "edit") editPreset(id);
        else if (action === "delete") deletePreset(id);
      };
    });

    presetListEl.querySelectorAll(".scene-item").forEach(function (row) {
      var id = row.getAttribute("data-id");
      row.onclick = function (e) {
        if (e.target.closest("button")) return;
        editPreset(id);
      };
    });
  }

  function applyPreset(id) {
    var path = "/apply/preset/" + encodeURIComponent(id);
    API.post(path, {})
      .then(function () {
        setStatus("Applied: " + id);
      })
      .catch(function (err) {
        setStatus("Apply failed: " + (err.message || "unknown"));
        if (typeof console !== "undefined" && console.error) console.error("[Presets] Apply failed:", path, err);
      });
  }

  function editPreset(id) {
    var preset = presets.find(function (p) {
      return p.id === id;
    });
    if (!preset) return;
    editingId = id;
    if (formTitle) formTitle.textContent = "Edit preset";
    setFormFromPreset(preset);
    if (cancelBtn) cancelBtn.style.display = "inline-flex";
  }

  function deletePreset(id) {
    if (!confirm('Delete preset "' + id + '"?')) return;
    API.delete("/presets/" + encodeURIComponent(id))
      .then(function () {
        presets = presets.filter(function (p) {
          return p.id !== id;
        });
        if (editingId === id) clearForm();
        renderPresetList();
        setStatus("Deleted.");
      })
      .catch(function (err) {
        setStatus("Delete failed: " + (err.message || "unknown"));
      });
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var payload = getFormPayload();
      if (!payload.id) {
        setStatus("Enter a name.");
        return;
      }
      var isEdit = editingId !== null;
      var method = isEdit ? "put" : "post";
      var path = isEdit
        ? "/presets/" + encodeURIComponent(editingId)
        : "/presets";
      API[method](path, payload)
        .then(function (saved) {
          if (isEdit) {
            var idx = presets.findIndex(function (p) {
              return p.id === saved.id;
            });
            if (idx >= 0) presets[idx] = saved;
            else presets.push(saved);
          } else {
            presets.push(saved);
          }
          clearForm();
          renderPresetList();
          setStatus("Preset saved.");
        })
        .catch(function (err) {
          setStatus("Save failed: " + (err.message || "unknown"));
        });
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      clearForm();
    });
  }

  document.addEventListener("DOMContentLoaded", loadData);
})();
