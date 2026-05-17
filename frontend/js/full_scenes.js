/**
 * Full scenes: combined scene + optional ILDA scene.
 */
(function () {
  "use strict";

  let fullScenes = [];
  let combinedScenes = [];
  let ildaScenes = [];
  let editingId = null;

  const form = document.getElementById("full-scene-form");
  const formTitle = document.getElementById("full-scene-form-title");
  const nameInput = document.getElementById("full-scene-name");
  const combinedSelect = document.getElementById("combined-scene");
  const ildaSelect = document.getElementById("ilda-scene");
  const cancelBtn = document.getElementById("btn-cancel-edit");
  const listEl = document.getElementById("full-scene-list");
  const statusEl = document.getElementById("full-scenes-status");

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

  function fillSelect(select, items, noneLabel) {
    if (!select) return;
    select.innerHTML = "";
    var none = document.createElement("option");
    none.value = "";
    none.textContent = noneLabel || "— None —";
    select.appendChild(none);
    items.forEach(function (item) {
      var opt = document.createElement("option");
      opt.value = item.id;
      opt.textContent = item.id;
      select.appendChild(opt);
    });
  }

  function loadData() {
    Promise.allSettled([
      API.get("/full-scenes"),
      API.get("/scenes"),
      API.get("/ilda-scenes")
    ]).then(function (outcomes) {
      fullScenes = outcomes[0].status === "fulfilled" ? outcomes[0].value || [] : [];
      combinedScenes = outcomes[1].status === "fulfilled" ? outcomes[1].value || [] : [];
      ildaScenes = outcomes[2].status === "fulfilled" ? outcomes[2].value || [] : [];
      fillSelect(combinedSelect, combinedScenes, "— Select —");
      fillSelect(ildaSelect, ildaScenes, "— None —");
      renderList();
      if (!combinedScenes.length) {
        setStatus("Create combined scenes on the Scenes page first.");
      } else if (!fullScenes.length) {
        setStatus("No full scenes saved yet.");
      } else {
        setStatus("");
      }
    });
  }

  function renderList() {
    if (!listEl) return;
    if (!fullScenes.length) {
      listEl.innerHTML = "";
      return;
    }
    listEl.innerHTML = fullScenes
      .map(function (fs) {
        var ildaLabel = fs.ilda_scene_id ? " · ILDA: " + fs.ilda_scene_id : "";
        return (
          '<div class="scene-item" data-id="' +
          fs.id +
          '"><div><span class="scene-item-name">' +
          fs.id +
          '</span><span class="scene-item-order">Scene: ' +
          (fs.scene_id || "") +
          ildaLabel +
          '</span></div><div><button type="button" class="btn btn-small btn-primary" data-apply="' +
          fs.id +
          '">Apply</button><button type="button" class="btn btn-small btn-secondary" data-edit="' +
          fs.id +
          '">Edit</button><button type="button" class="btn btn-small btn-danger" data-delete="' +
          fs.id +
          '">Delete</button></div></div>'
        );
      })
      .join("");

    listEl.querySelectorAll("[data-apply]").forEach(function (btn) {
      btn.onclick = function () {
        API.post("/apply/full-scene/" + encodeURIComponent(btn.getAttribute("data-apply")), {})
          .then(function () {
            setStatus("Applied on server. Open Active to use beat sync.");
          })
          .catch(function (err) {
            setStatus("Apply failed: " + (err.message || "unknown"));
          });
      };
    });
    listEl.querySelectorAll("[data-edit]").forEach(function (btn) {
      btn.onclick = function () {
        editFullScene(btn.getAttribute("data-edit"));
      };
    });
    listEl.querySelectorAll("[data-delete]").forEach(function (btn) {
      btn.onclick = function () {
        var id = btn.getAttribute("data-delete");
        if (!confirm('Delete full scene "' + id + '"?')) return;
        API.delete("/full-scenes/" + encodeURIComponent(id)).then(loadData);
      };
    });
  }

  function clearForm() {
    editingId = null;
    if (formTitle) formTitle.textContent = "New full scene";
    if (nameInput) nameInput.value = "";
    if (combinedSelect) combinedSelect.value = "";
    if (ildaSelect) ildaSelect.value = "";
    if (cancelBtn) cancelBtn.style.display = "none";
  }

  function editFullScene(id) {
    var fs = fullScenes.find(function (s) {
      return s.id === id;
    });
    if (!fs) return;
    editingId = id;
    if (formTitle) formTitle.textContent = "Edit full scene";
    if (nameInput) nameInput.value = fs.id;
    if (combinedSelect) combinedSelect.value = fs.scene_id || "";
    if (ildaSelect) ildaSelect.value = fs.ilda_scene_id || "";
    if (cancelBtn) cancelBtn.style.display = "inline-flex";
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = (nameInput && nameInput.value.trim()) || "";
      var id = editingId !== null ? editingId : slugify(name);
      var sceneId = combinedSelect && combinedSelect.value;
      if (!id || !sceneId) {
        setStatus("Enter a name and select a combined scene.");
        return;
      }
      var payload = {
        id: id,
        scene_id: sceneId,
        ilda_scene_id: (ildaSelect && ildaSelect.value) || ""
      };
      var isEdit = editingId !== null;
      var path = isEdit ? "/full-scenes/" + encodeURIComponent(editingId) : "/full-scenes";
      API[isEdit ? "put" : "post"](path, payload)
        .then(function () {
          clearForm();
          setStatus("Full scene saved.");
          loadData();
        })
        .catch(function (err) {
          setStatus("Save failed: " + (err.message || "unknown"));
        });
    });
  }

  if (cancelBtn) cancelBtn.addEventListener("click", clearForm);

  document.addEventListener("DOMContentLoaded", loadData);
})();
