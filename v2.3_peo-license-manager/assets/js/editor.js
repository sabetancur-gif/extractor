/* global PEO */
/* editor.js — modal de edición de campos con live preview del PDF */
"use strict";

// Debounce para re-render del live preview mientras el usuario escribe
const _debouncedLivePreview = PEO.debounce(_updateLivePreview, 180);

async function _updateLivePreview() {
  if (!PEO.state.preview.row || !PEO.state.preview.templateBytes) return;
  const token  = ++PEO.state.preview.renderToken;
  const iframe = PEO.$("livePreviewFrame"); if (!iframe) return;
  const bytes  = await PEO.fillPdf(PEO.state.preview.templateBytes, PEO.state.preview.row, { flatten: false });
  const url    = PEO.blobUrl(bytes);
  if (token !== PEO.state.preview.renderToken) { URL.revokeObjectURL(url); return; }
  if (PEO.state.preview.liveUrl) URL.revokeObjectURL(PEO.state.preview.liveUrl);
  PEO.state.preview.liveUrl = url;
  iframe.src = url;
}

// ── Construcción del formulario de edición ─────────────────────────────────
PEO.buildEditor = function(row) {
  const ctrl      = new Set(["# case", "creado", "estado", "proceso"]);
  const container = document.createElement("div");
  container.className = "preview-fields";
  const keys = [...PEO.state.preview.fieldTypes.keys()].filter(n => !ctrl.has(n));

  if (!keys.length) {
    container.innerHTML = "<p style='font-size:12px;color:var(--muted)'>No editable fields.</p>";
    return container;
  }

  for (const n of keys) {
    const [val, src]  = PEO.getEffectiveValue(row, n);
    const ft          = PEO.state.preview.fieldTypes.get(n);
    const isReq       = PEO.state.preview.requiredFields.has(n);
    const isEmpty     = !val;
    const wrap        = document.createElement("div");
    wrap.className    = "preview-field";
    wrap.dataset.search = `${n} ${ft}`;

    const reqMark  = isReq    ? `<span style="color:var(--alert)"> *</span>` : "";
    const srcTag   = src === "default" ? `<span style="font-size:9px;color:var(--add);margin-left:3px">[default]</span>` : "";
    const warnTag  = isReq && isEmpty  ? `<span style="font-size:9px;color:var(--alert);margin-left:3px">⚠ required</span>` : "";
    wrap.innerHTML = `<label>${PEO.esc(n.replace(/_/g, " "))}${reqMark}${srcTag}${warnTag}</label>`;

    if (ft === "PDFCheckBox") {
      const inp  = document.createElement("input");
      inp.type   = "checkbox";
      inp.checked = ["si","sí","yes","true","1","x"].includes(val.toLowerCase());
      inp.addEventListener("change", () => {
        PEO.setRowValue(row, n, inp.checked ? "SI" : "");
        _debouncedLivePreview();
      });
      wrap.appendChild(inp);
    } else {
      const inp = document.createElement("input");
      inp.type  = "text";
      inp.value = val;
      if (src === "default") inp.style.color = "var(--add)";
      if (isReq && isEmpty)  inp.style.borderColor = "var(--alert)";
      inp.addEventListener("input", PEO.debounce(() => {
        PEO.setRowValue(row, n, inp.value);
        if (inp.value.trim()) inp.style.borderColor = "";
        _updateLivePreview();
      }, 180));
      wrap.appendChild(inp);
    }
    container.appendChild(wrap);
  }
  return container;
};

// ── Abrir modal de edición ─────────────────────────────────────────────────
PEO.openEditModal = async function(row) {
  const tf   = PEO.getTemplateFile(String(PEO.getRowValue(row, "Estado")), String(PEO.getRowValue(row, "Proceso")));
  const tb   = await tf.arrayBuffer();
  const meta = await PEO.getPdfMeta(tb);
  PEO.state.preview.row           = row;
  PEO.state.preview.templateBytes = tb;
  PEO.state.preview.fieldTypes    = meta.fieldTypes;
  PEO.state.preview.requiredFields = meta.requiredFields;
  PEO.state.preview.renderToken   = 0;

  const cv = String(PEO.getRowValue(row, "# Case")).trim();
  PEO.els.editModalBody.innerHTML = `
    <div style="display:flex;height:100%;overflow:hidden">
      <!-- Panel izquierdo: iframe del PDF -->
      <div style="flex:1;border-right:1px solid var(--border);position:relative;overflow:hidden">
        <iframe id="livePreviewFrame" style="width:100%;height:100%;border:none"></iframe>
      </div>
      <!-- Panel derecho: 3 zonas -->
      <div style="width:320px;display:flex;flex-direction:column;height:100%;overflow:hidden">
        <!-- Zona 1: Header fijo — título, leyenda, buscador -->
        <div style="padding:18px 18px 12px;flex-shrink:0;border-bottom:1px solid var(--border);display:flex;flex-direction:column;gap:8px">
          <div style="font-size:14px;font-weight:700">
            Edit &nbsp;<span style="color:var(--add)">#${PEO.esc(cv)}</span>
          </div>
          <div style="font-size:11px;color:var(--muted);line-height:1.6">
            <span style="color:var(--add)">Azul</span> = valor de defaults.json &nbsp;·&nbsp;
            <span style="color:var(--alert)">*</span> = campo requerido
          </div>
          <input id="fieldSearchEdit" class="field-search" type="text"
                  placeholder="Buscar campo…"
                  style="width:100%;padding:7px 10px;border:1px solid var(--border);
                        border-radius:var(--radius);background:var(--surface2);
                        color:var(--text);font-size:12px;font-family:inherit">
        </div>
        <!-- Zona 2: Campos con scroll — solo esta parte se desplaza -->
        <div id="editorFieldsEdit"
              style="flex:1;overflow-y:auto;padding:12px 18px;
                    display:flex;flex-direction:column;gap:6px;
                    scrollbar-width:thin;scrollbar-color:var(--border2) transparent">
        </div>
        <!-- Zona 3: Footer fijo — botones siempre visibles -->
        <div style="padding:12px 18px;border-top:1px solid var(--border);
                    flex-shrink:0;display:flex;gap:6px">
          <button class="main-btn cta" id="applyEditBtn" style="flex:1">Guardar y volver</button>
          <button class="main-btn"    id="closeEditBtn">Cerrar</button>
        </div>
      </div>
    </div>`;

  PEO.els.editModalOverlay.classList.add("open");
  PEO.$("editorFieldsEdit").appendChild(PEO.buildEditor(row));

  PEO.$("fieldSearchEdit").addEventListener("input", e => {
    const q = PEO.norm(e.target.value).replace(/\s+/g, "_");
    document.querySelectorAll("#editorFieldsEdit .preview-field").forEach(el => {
      el.style.display = PEO.norm(el.dataset.search || "").includes(q) ? "" : "none";
    });
  });

  PEO.$("applyEditBtn").addEventListener("click", () => {
    PEO.closeEditModal();
    PEO.refreshAll();
    PEO.notify("Changes applied.", "ok");
  });
  PEO.$("closeEditBtn").addEventListener("click", PEO.closeEditModal);

  await _updateLivePreview();
};

PEO.closeEditModal = function() {
  PEO.els.editModalOverlay.classList.remove("open");
  PEO.els.editModalBody.innerHTML = "";
  if (PEO.state.preview.liveUrl) {
    URL.revokeObjectURL(PEO.state.preview.liveUrl);
    PEO.state.preview.liveUrl = "";
  }
  PEO.state.preview.row = null;
};
