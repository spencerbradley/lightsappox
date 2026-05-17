/**
 * ILDA frames catalog and ILDA scenes (ordered frames, beat or timed).
 */
(function () {
  "use strict";

  let frames = [];
  let ildaScenes = [];
  let editingIldaId = null;
  let orderFrameIds = [];

  const frameForm = document.getElementById("frame-form");
  const frameIdInput = document.getElementById("frame-id");
  const framePathInput = document.getElementById("frame-path");
  const frameListEl = document.getElementById("frame-list");
  const framesStatusEl = document.getElementById("frames-status");

  const ildaForm = document.getElementById("ilda-scene-form");
  const ildaFormTitle = document.getElementById("ilda-scene-form-title");
  const ildaNameInput = document.getElementById("ilda-scene-name");
  const ildaFrameOrderEl = document.getElementById("ilda-frame-order");
  const addFrameSelect = document.getElementById("add-frame-select");
  const btnAddFrame = document.getElementById("btn-add-frame");
  const beatSyncedInput = document.getElementById("ilda-beat-synced");
  const timeStepInput = document.getElementById("ilda-time-step");
  const cancelIldaBtn = document.getElementById("btn-cancel-ilda-edit");
  const ildaSceneListEl = document.getElementById("ilda-scene-list");
  const ildaScenesStatusEl = document.getElementById("ilda-scenes-status");

  function slugify(str) {
    return str
      .toLowerCase()
      .trim()
      .replace(/\s+/g, "_")
      .replace(/[^a-z0-9_]/g, "");
  }

  function setFramesStatus(msg) {
    if (framesStatusEl) framesStatusEl.textContent = msg;
  }

  function setIldaStatus(msg) {
    if (ildaScenesStatusEl) ildaScenesStatusEl.textContent = msg;
  }

  function loadData() {
    Promise.allSettled([API.get("/ilda-frames"), API.get("/ilda-scenes")]).then(function (outcomes) {
      frames = outcomes[0].status === "fulfilled" ? outcomes[0].value || [] : [];
      ildaScenes = outcomes[1].status === "fulfilled" ? outcomes[1].value || [] : [];
      renderFrameList();
      renderAddFrameOptions();
      renderIldaSceneList();
      setIldaStatus(ildaScenes.length ? "" : "No ILDA scenes yet.");
    });
  }

  function renderFrameList() {
    if (!frameListEl) return;
    if (!frames.length) {
      frameListEl.innerHTML = '<p class="placeholder-note">No frames registered.</p>';
      return;
    }
    frameListEl.innerHTML = frames
      .map(function (f) {
        return (
          '<div class="scene-item" data-id="' +
          f.id +
          '"><div><span class="scene-item-name">' +
          f.id +
          '</span><span class="scene-item-order">' +
          (f.path || "") +
          '</span></div><div><button type="button" class="btn btn-small btn-danger" data-delete-frame="' +
          f.id +
          '">Delete</button></div></div>'
        );
      })
      .join("");
    frameListEl.querySelectorAll("[data-delete-frame]").forEach(function (btn) {
      btn.onclick = function () {
        var id = btn.getAttribute("data-delete-frame");
        if (!confirm('Delete frame "' + id + '"?')) return;
        API.delete("/ilda-frames/" + encodeURIComponent(id)).then(loadData);
      };
    });
  }

  function renderAddFrameOptions() {
    if (!addFrameSelect) return;
    addFrameSelect.innerHTML = '<option value="">— Add frame —</option>';
    frames.forEach(function (f) {
      var opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = f.id;
      addFrameSelect.appendChild(opt);
    });
  }

  function renderOrderList() {
    if (!ildaFrameOrderEl) return;
    if (!orderFrameIds.length) {
      ildaFrameOrderEl.innerHTML = '<p class="placeholder-note">No frames. Add below.</p>';
      return;
    }
    ildaFrameOrderEl.innerHTML = orderFrameIds
      .map(function (fid, index) {
        var up = index > 0 ? '<button type="button" class="btn btn-small btn-secondary" data-action="up" data-index="' + index + '">↑</button>' : "";
        var down =
          index < orderFrameIds.length - 1
            ? '<button type="button" class="btn btn-small btn-secondary" data-action="down" data-index="' + index + '">↓</button>'
            : "";
        return (
          '<div class="scene-preset-row" data-index="' +
          index +
          '"><span>' +
          fid +
          '</span><div>' +
          up +
          down +
          '<button type="button" class="btn btn-small btn-danger" data-action="remove" data-index="' +
          index +
          '">Remove</button></div></div>'
        );
      })
      .join("");
    ildaFrameOrderEl.querySelectorAll("[data-action]").forEach(function (btn) {
      var action = btn.getAttribute("data-action");
      var index = parseInt(btn.getAttribute("data-index"), 10);
      btn.onclick = function () {
        if (action === "up" && index > 0) {
          orderFrameIds.splice(index - 1, 0, orderFrameIds.splice(index, 1)[0]);
          renderOrderList();
        } else if (action === "down" && index < orderFrameIds.length - 1) {
          orderFrameIds.splice(index + 1, 0, orderFrameIds.splice(index, 1)[0]);
          renderOrderList();
        } else if (action === "remove") {
          orderFrameIds.splice(index, 1);
          renderOrderList();
        }
      };
    });
  }

  function renderIldaSceneList() {
    if (!ildaSceneListEl) return;
    if (!ildaScenes.length) {
      ildaSceneListEl.innerHTML = "";
      return;
    }
    ildaSceneListEl.innerHTML = ildaScenes
      .map(function (s) {
        var order = (s.ilda_frames || []).join(" → ");
        var mode = s.beat_synced ? "beat" : "every " + s.time_step + "s";
        return (
          '<div class="scene-item" data-id="' +
          s.id +
          '"><div><span class="scene-item-name">' +
          s.id +
          '</span><span class="scene-item-order">' +
          (order || "(no frames)") +
          " · " +
          mode +
          '</span></div><div><button type="button" class="btn btn-small btn-secondary" data-edit-ilda="' +
          s.id +
          '">Edit</button><button type="button" class="btn btn-small btn-danger" data-delete-ilda="' +
          s.id +
          '">Delete</button></div></div>'
        );
      })
      .join("");
    ildaSceneListEl.querySelectorAll("[data-edit-ilda]").forEach(function (btn) {
      btn.onclick = function () {
        editIldaScene(btn.getAttribute("data-edit-ilda"));
      };
    });
    ildaSceneListEl.querySelectorAll("[data-delete-ilda]").forEach(function (btn) {
      btn.onclick = function () {
        var id = btn.getAttribute("data-delete-ilda");
        if (!confirm('Delete ILDA scene "' + id + '"?')) return;
        API.delete("/ilda-scenes/" + encodeURIComponent(id)).then(loadData);
      };
    });
  }

  function clearIldaForm() {
    editingIldaId = null;
    orderFrameIds = [];
    if (ildaFormTitle) ildaFormTitle.textContent = "New ILDA scene";
    if (ildaNameInput) ildaNameInput.value = "";
    if (beatSyncedInput) beatSyncedInput.checked = true;
    if (timeStepInput) timeStepInput.value = "0.1";
    if (cancelIldaBtn) cancelIldaBtn.style.display = "none";
    renderOrderList();
  }

  function editIldaScene(id) {
    var scene = ildaScenes.find(function (s) {
      return s.id === id;
    });
    if (!scene) return;
    editingIldaId = id;
    if (ildaFormTitle) ildaFormTitle.textContent = "Edit ILDA scene";
    if (ildaNameInput) ildaNameInput.value = scene.id;
    orderFrameIds = (scene.ilda_frames || []).slice();
    if (beatSyncedInput) beatSyncedInput.checked = !!scene.beat_synced;
    if (timeStepInput) timeStepInput.value = String(scene.time_step != null ? scene.time_step : 0.1);
    if (cancelIldaBtn) cancelIldaBtn.style.display = "inline-flex";
    renderOrderList();
  }

  if (frameForm) {
    frameForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var id = (frameIdInput && frameIdInput.value.trim()) || "";
      var path = (framePathInput && framePathInput.value.trim()) || "";
      if (!id || !path) {
        setFramesStatus("Enter frame id and path.");
        return;
      }
      API.post("/ilda-frames", { id: id, path: path })
        .then(function () {
          if (frameIdInput) frameIdInput.value = "";
          if (framePathInput) framePathInput.value = "";
          setFramesStatus("Frame saved.");
          loadData();
        })
        .catch(function (err) {
          setFramesStatus("Save failed: " + (err.message || "unknown"));
        });
    });
  }

  if (btnAddFrame) {
    btnAddFrame.addEventListener("click", function () {
      var val = addFrameSelect && addFrameSelect.value;
      if (!val) return;
      orderFrameIds.push(val);
      renderOrderList();
      if (addFrameSelect) addFrameSelect.value = "";
    });
  }

  if (ildaForm) {
    ildaForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = (ildaNameInput && ildaNameInput.value.trim()) || "";
      var id = editingIldaId !== null ? editingIldaId : slugify(name);
      if (!id) {
        setIldaStatus("Enter a name.");
        return;
      }
      var payload = {
        id: id,
        ilda_frames: orderFrameIds.slice(),
        beat_synced: !!(beatSyncedInput && beatSyncedInput.checked),
        time_step: parseFloat(timeStepInput && timeStepInput.value) || 0.1
      };
      var isEdit = editingIldaId !== null;
      var path = isEdit ? "/ilda-scenes/" + encodeURIComponent(editingIldaId) : "/ilda-scenes";
      API[isEdit ? "put" : "post"](path, payload)
        .then(function () {
          clearIldaForm();
          setIldaStatus("ILDA scene saved.");
          loadData();
        })
        .catch(function (err) {
          setIldaStatus("Save failed: " + (err.message || "unknown"));
        });
    });
  }

  if (cancelIldaBtn) cancelIldaBtn.addEventListener("click", clearIldaForm);

  document.addEventListener("DOMContentLoaded", function () {
    loadData();
    renderOrderList();
  });
})();
