/**
 * Scenes page: ordered list of presets per scene. Save, delete, apply, reorder.
 */
(function () {
  "use strict";

  let scenes = [];
  let presets = [];
  let editingId = null;
  let orderPresetIds = []; // current form order

  const form = document.getElementById("scene-form");
  const formTitle = document.getElementById("scene-form-title");
  const nameInput = document.getElementById("scene-name");
  const presetListRoot = document.getElementById("scene-preset-list");
  const addPresetSelect = document.getElementById("add-preset-select");
  const btnAddPreset = document.getElementById("btn-add-preset");
  const cancelBtn = document.getElementById("btn-cancel-edit");
  const sceneListEl = document.getElementById("scene-list");
  const statusEl = document.getElementById("scenes-status");

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

  function loadData() {
    Promise.allSettled([API.get("/scenes"), API.get("/presets")])
      .then(function (outcomes) {
        scenes = outcomes[0].status === "fulfilled" ? (outcomes[0].value || []) : [];
        presets = outcomes[1].status === "fulfilled" ? (outcomes[1].value || []) : [];
        renderAddPresetOptions();
        renderSceneList();
        var errors = [];
        if (outcomes[0].status === "rejected") errors.push("scenes: " + (outcomes[0].reason && outcomes[0].reason.message));
        if (outcomes[1].status === "rejected") errors.push("presets: " + (outcomes[1].reason && outcomes[1].reason.message));
        if (errors.length) {
          setStatus("Partial load: " + errors.join("; "));
          console.error("Scenes page load errors:", outcomes);
        } else {
          setStatus("");
        }
      })
      .catch(function (err) {
        setStatus("Failed to load: " + (err.message || "unknown"));
        console.error(err);
      });
  }

  function renderAddPresetOptions() {
    if (!addPresetSelect) return;
    var first = addPresetSelect.querySelector("option");
    addPresetSelect.innerHTML = "";
    if (first) addPresetSelect.appendChild(first);
    else {
      var none = document.createElement("option");
      none.value = "";
      none.textContent = "— Add preset —";
      addPresetSelect.appendChild(none);
    }
    presets.forEach(function (p) {
      var opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.id;
      addPresetSelect.appendChild(opt);
    });
  }

  function renderOrderList() {
    if (!presetListRoot) return;
    if (orderPresetIds.length === 0) {
      presetListRoot.innerHTML = '<p class="placeholder-note">No presets. Add presets below.</p>';
      return;
    }
    presetListRoot.innerHTML = orderPresetIds
      .map(function (presetId, index) {
        var up = index > 0 ? '<button type="button" class="btn btn-small btn-secondary" data-action="up" data-index="' + index + '">↑</button>' : "";
        var down = index < orderPresetIds.length - 1 ? '<button type="button" class="btn btn-small btn-secondary" data-action="down" data-index="' + index + '">↓</button>' : "";
        return (
          '<div class="scene-preset-row" data-index="' +
          index +
          '">' +
          "<span>" +
          presetId +
          "</span>" +
          "<div>" +
          up +
          down +
          '<button type="button" class="btn btn-small btn-danger" data-action="remove" data-index="' +
          index +
          '">Remove</button>' +
          "</div>" +
          "</div>"
        );
      })
      .join("");

    presetListRoot.querySelectorAll("[data-action]").forEach(function (btn) {
      var action = btn.getAttribute("data-action");
      var index = parseInt(btn.getAttribute("data-index"), 10);
      btn.onclick = function () {
        if (action === "up" && index > 0) {
          orderPresetIds.splice(index - 1, 0, orderPresetIds.splice(index, 1)[0]);
          renderOrderList();
        } else if (action === "down" && index < orderPresetIds.length - 1) {
          orderPresetIds.splice(index + 1, 0, orderPresetIds.splice(index, 1)[0]);
          renderOrderList();
        } else if (action === "remove") {
          orderPresetIds.splice(index, 1);
          renderOrderList();
        }
      };
    });
  }

  function addPresetToOrder() {
    var val = addPresetSelect && addPresetSelect.value;
    if (!val) return;
    orderPresetIds.push(val);
    renderOrderList();
    if (addPresetSelect) addPresetSelect.value = "";
  }

  function clearForm() {
    editingId = null;
    orderPresetIds = [];
    if (formTitle) formTitle.textContent = "New scene";
    if (nameInput) nameInput.value = "";
    renderOrderList();
    if (cancelBtn) cancelBtn.style.display = "none";
  }

  function renderSceneList() {
    if (!sceneListEl) return;
    if (scenes.length === 0) {
      sceneListEl.innerHTML = "";
      setStatus("No scenes saved yet.");
      return;
    }
    setStatus("");
    sceneListEl.innerHTML = scenes
      .map(function (s) {
        var order = (s.preset_ids || []).join(" → ");
        return (
          '<div class="scene-item" data-id="' +
          s.id +
          '">' +
          "<div>" +
          "<span class=\"scene-item-name\">" +
          s.id +
          "</span>" +
          '<span class="scene-item-order">' +
          (order || "(no presets)") +
          "</span>" +
          "</div>" +
          "<div>" +
          '<button type="button" class="btn btn-small btn-primary" data-action="apply" data-id="' +
          s.id +
          '">Apply</button>' +
          '<button type="button" class="btn btn-small btn-secondary" data-action="edit" data-id="' +
          s.id +
          '">Edit</button>' +
          '<button type="button" class="btn btn-small btn-danger" data-action="delete" data-id="' +
          s.id +
          '">Delete</button>' +
          "</div>" +
          "</div>"
        );
      })
      .join("");

    sceneListEl.querySelectorAll("[data-action]").forEach(function (btn) {
      var action = btn.getAttribute("data-action");
      var id = btn.getAttribute("data-id");
      btn.onclick = function (e) {
        e.stopPropagation();
        if (action === "apply") applyScene(id);
        else if (action === "edit") editScene(id);
        else if (action === "delete") deleteScene(id);
      };
    });

    sceneListEl.querySelectorAll(".scene-item").forEach(function (row) {
      var id = row.getAttribute("data-id");
      row.onclick = function (e) {
        if (e.target.closest("button")) return;
        editScene(id);
      };
    });
  }

  function applyScene(id) {
    API.post("/apply/scene/" + encodeURIComponent(id))
      .then(function () {
        setStatus("Applied: " + id);
      })
      .catch(function (err) {
        setStatus("Apply failed: " + (err.message || "unknown"));
      });
  }

  function editScene(id) {
    var scene = scenes.find(function (s) {
      return s.id === id;
    });
    if (!scene) return;
    editingId = id;
    if (formTitle) formTitle.textContent = "Edit scene";
    if (nameInput) nameInput.value = scene.id;
    orderPresetIds = (scene.preset_ids || []).slice();
    renderOrderList();
    if (cancelBtn) cancelBtn.style.display = "inline-flex";
  }

  function deleteScene(id) {
    if (!confirm('Delete scene "' + id + '"?')) return;
    API.delete("/scenes/" + encodeURIComponent(id))
      .then(function () {
        scenes = scenes.filter(function (s) {
          return s.id !== id;
        });
        if (editingId === id) clearForm();
        renderSceneList();
        setStatus("Deleted.");
      })
      .catch(function (err) {
        setStatus("Delete failed: " + (err.message || "unknown"));
      });
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = (nameInput && nameInput.value.trim()) || "";
      var id = editingId !== null ? editingId : slugify(name);
      if (!id) {
        setStatus("Enter a name.");
        return;
      }
      var payload = { id: id, preset_ids: orderPresetIds.slice() };
      var isEdit = editingId !== null;
      var path = isEdit ? "/scenes/" + encodeURIComponent(editingId) : "/scenes";
      var method = isEdit ? "put" : "post";
      API[method](path, payload)
        .then(function (saved) {
          if (isEdit) {
            var idx = scenes.findIndex(function (s) {
              return s.id === saved.id;
            });
            if (idx >= 0) scenes[idx] = saved;
            else scenes.push(saved);
          } else {
            scenes.push(saved);
          }
          clearForm();
          renderSceneList();
          setStatus("Scene saved.");
        })
        .catch(function (err) {
          setStatus("Save failed: " + (err.message || "unknown"));
        });
    });
  }

  if (btnAddPreset) btnAddPreset.addEventListener("click", addPresetToOrder);
  if (cancelBtn) cancelBtn.addEventListener("click", clearForm);

  document.addEventListener("DOMContentLoaded", function () {
    loadData();
    renderOrderList();
  });
})();
