/* global PEO */
/* app.js — punto de entrada: eventos, inicialización, arranque */
"use strict";

function on(id, ev, fn) {
  const el = PEO.$(id);
  if (el) el.addEventListener(ev, fn);
}

function attachEvents() {
  // ── Carrusel de operador ────────────────────────────────────────────────
  ;(function initCarousel() {
    const ops    = PEO.OPERATORS;           // viene de config.js
    const SHOW   = 4;                       // siempre 4 visibles
    let   start  = 0;                       // índice del primer card visible

    function render() {
      const track = document.getElementById("carouselTrack");
      const dots  = document.getElementById("carouselDots");
      if (!track || !dots) return;

      // ── Cards visibles ─────────────────────────────────────────────────
      track.innerHTML = "";
      const visibleIdxs = [];
      for (let i = 0; i < SHOW; i++) {
        visibleIdxs.push((start + i) % ops.length);
      }

      visibleIdxs.forEach(idx => {
        const name   = ops[idx];
        const active = name === PEO.state.selectedUser;
        const card   = document.createElement("button");
        card.type        = "button";
        card.className   = "user-card" + (active ? " active" : "");
        card.dataset.user = name;
        card.innerHTML   = `
          <div class="user-card-avatar">${name.trim().split(/\s+/).map(n => n.charAt(0)).join("").toUpperCase()}</div>
          <div class="user-card-name">${name}</div>`;
        card.addEventListener("click", () => {
          PEO.state.selectedUser = name;
          render();
          const errEl = PEO.$("loadError");
          if (errEl && errEl.dataset.reason === "no-user") errEl.style.display = "none";
          document.getElementById("userSelector")?.classList.remove("shake");
        });
        track.appendChild(card);
      });

      // ── Dots de posición + selección ───────────────────────────────────
      dots.innerHTML = "";
      ops.forEach((name, i) => {
        const dot      = document.createElement("button");
        dot.type       = "button";
        dot.title      = name;
        dot.setAttribute("aria-label", name);
        const isSelected = name === PEO.state.selectedUser;
        const isVisible  = visibleIdxs.includes(i);
        dot.className  = "carousel-dot"
          + (isSelected ? " selected" : "")
          + (!isSelected && isVisible ? " visible" : "");
        dot.addEventListener("click", () => {
          // Navegar para que este operador quede visible y seleccionarlo
          start = i;
          PEO.state.selectedUser = ops[i];
          render();
        });
        dots.appendChild(dot);
      });
    }

    // Flechas
    document.getElementById("carouselPrev")?.addEventListener("click", () => {
      start = (start - 1 + ops.length) % ops.length;
      render();
    });
    document.getElementById("carouselNext")?.addEventListener("click", () => {
      start = (start + 1) % ops.length;
      render();
    });

    // Teclado: ← → dentro del carrusel
    document.getElementById("userSelector")?.addEventListener("keydown", e => {
      if (e.key === "ArrowLeft")  { start = (start - 1 + ops.length) % ops.length; render(); }
      if (e.key === "ArrowRight") { start = (start + 1) % ops.length; render(); }
    });

    render(); // pintado inicial
  })();

  // ── Carga de carpeta / archivos individuales ────────────────────────────
  async function handleFiles(fl) {
    const files  = [...fl]; if (!files.length) return;
    const errEl  = PEO.$("loadError");
    // Validación: Usuario obligatorio antes de cargar
    if (!PEO.state.selectedUser) {
      if (errEl) {
        errEl.textContent     = "Select your name before uploading the folder.";
        errEl.dataset.reason  = "no-user";
        errEl.style.display   = "block";
      }
      const sel = document.getElementById("userSelector");
      sel?.classList.remove("shake");
      void sel?.offsetWidth;    // fuerza reflow para reiniciar la animación
      sel?.classList.add("shake");
      return;
    }
    try {
      if (errEl) errEl.style.display = "none";
      await PEO.loadFolder(files);
    } catch(e) {
      PEO.notify(e.message, "err");
      if (errEl) { errEl.textContent = e.message; errEl.dataset.reason = "load"; errEl.style.display = "block"; }
    }
  }

  PEO.els.folderInput.addEventListener("change", () => handleFiles(PEO.els.folderInput.files));
  const fi = PEO.$("filesInput");
  if (fi) fi.addEventListener("change", () => handleFiles(fi.files));

  // ── Preview navigation ──────────────────────────────────────────────────
  on("previewPrevBtn", "click", async () => {
    if (PEO.state.preview.index > 0) await PEO.renderPreviewAt(PEO.state.preview.index - 1);
  });
  on("previewNextBtn", "click", async () => {
    if (PEO.state.preview.index < PEO.state.preview.items.length - 1)
      await PEO.renderPreviewAt(PEO.state.preview.index + 1);
  });
  on("closePreviewModal", "click", PEO.closePreviewModal);

  // ── Edit modal — cerrar al click en el overlay ──────────────────────────
  on("editModalOverlay", "click", e => {
    if (e.target === PEO.$("editModalOverlay")) PEO.closeEditModal();
  });

  // ── Output folder (File System Access API) ──────────────────────────────
  on("btnPickOutput", "click", async () => {
    try {
      PEO.state.outputDirHandle = await window.showDirectoryPicker();
      PEO.state.outputDirLabel  = PEO.state.outputDirHandle.name || "folder";
      const btn = PEO.$("btnPickOutput");
      if (btn) btn.textContent = `📁 ${PEO.state.outputDirLabel}`;
      PEO.notify("Output folder set: " + PEO.state.outputDirLabel, "ok");
    } catch {}
  });

  // ── Acciones del header ─────────────────────────────────────────────────
  on("btnSaveWorkbook",  "click", PEO.saveWorkbookToDisk);
  on("btnEditDefaults",  "click", PEO.openDefaultsModal);
  on("defaultsSaveBtn",  "click", PEO.saveDefaultsFromModal);
  on("defaultsCancelBtn","click", () => PEO.els.defaultsModal.classList.remove("open"));
  on("btnTheme",         "click", PEO.toggleTheme);

  // ── Teclado: Escape cierra modales, ← → navegan preview ───────────────
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      if (PEO.els.previewModal.style.display === "flex") { PEO.closePreviewModal(); return; }
      if (PEO.els.editModalOverlay.classList.contains("open")) { PEO.closeEditModal(); return; }
      if (PEO.els.defaultsModal.classList.contains("open"))    { PEO.els.defaultsModal.classList.remove("open"); return; }
    }
    if (PEO.els.previewModal.style.display !== "flex") return;
    if (document.activeElement && ["INPUT","TEXTAREA"].includes(document.activeElement.tagName)) return;
    if (e.key === "ArrowLeft"  && !PEO.els.previewPrevBtn.disabled) PEO.renderPreviewAt(PEO.state.preview.index - 1);
    if (e.key === "ArrowRight" && PEO.state.preview.index < PEO.state.preview.items.length - 1)
      PEO.renderPreviewAt(PEO.state.preview.index + 1);
  });
}

// ── Inicialización ─────────────────────────────────────────────────────────
// Exponer funciones que el HTML llama con onclick=""
window._peo = {
  previewState:     PEO.previewState,
  generateState:    PEO.generateState,
  validateTemplate: PEO.validateTemplate,
};

attachEvents();
PEO.$("versionLabel").textContent = PEO.VERSION;
PEO.initTheme();

const _stopLoadCA = PEO.startLoadCA("loadCanvas");
PEO.startHeaderCA("headerCanvas");

document.addEventListener("peo-folder-loaded", () => {
  _stopLoadCA();
  const lc = PEO.$("loadCanvas");
  if (lc) lc.style.display = "none";
}, { once: true });
