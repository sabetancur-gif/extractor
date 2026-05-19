/* global PEO */
/* preview.js — modal de previsualización de PDFs llenados */
"use strict";

// ── Abrir preview para un estado y proceso ─────────────────────────────────
PEO.previewState = async function(abbr, proceso) {
  try {
    const d = PEO.buildStateMap(PEO.state.currentRows)[abbr];
    if (!d) { PEO.notify("No pending records for " + abbr, "err"); return; }
    const rows = proceso === "ADD" ? d.adds : d.terms;
    if (!rows.length) { PEO.notify("No pending " + proceso + " records", "err"); return; }
    const tf   = PEO.getTemplateFile(d.fullName, proceso);
    const tb   = await tf.arrayBuffer();
    const meta = await PEO.getPdfMeta(tb);
    PEO.state.preview = {
      ...PEO.state.preview,
      items: rows, index: 0,
      templateBytes: tb, fieldTypes: meta.fieldTypes, requiredFields: meta.requiredFields,
      _abbr: abbr, _proceso: proceso,
    };
    PEO.els.previewModal.style.display = "flex";
    await PEO.renderPreviewAt(0);
  } catch(e) { PEO.notify(e.message, "err"); }
};

// ── Renderizar registro en posición index ──────────────────────────────────
PEO.renderPreviewAt = async function(index) {
  const row   = PEO.state.preview.items[index]; if (!row) return;
  const total = PEO.state.preview.items.length;
  const isLast = index >= total - 1;
  PEO.state.preview.index = index;

  const bytes = await PEO.fillPdf(PEO.state.preview.templateBytes, row, { flatten: false });
  const url   = PEO.blobUrl(bytes);
  if (PEO.state.preview.liveUrl) URL.revokeObjectURL(PEO.state.preview.liveUrl);
  PEO.state.preview.liveUrl = url;
  PEO.els.previewSingleFrame.src = url;

  // Header del modal
  const cv = String(PEO.getRowValue(row, "# Case")).trim();
  PEO.els.previewCaseTitle.textContent = `Case #${cv}`;
  const sl = PEO.$("previewStateLabel");
  if (sl) sl.textContent = `${PEO.getRowValue(row, "Estado")} · ${PEO.getRowValue(row, "Proceso")}`;
  PEO.els.previewCounter.textContent = `${index + 1} of ${total}`;
  PEO.els.previewPrevBtn.disabled = index <= 0;

  // Step dots (máx 12 visibles)
  const dotsEl = PEO.$("previewDots");
  if (dotsEl) {
    dotsEl.innerHTML = "";
    const show   = Math.min(total, 12);
    const offset = total > 12 ? Math.max(0, Math.min(index - 5, total - 12)) : 0;
    for (let i = offset; i < offset + show; i++) {
      const dot = document.createElement("div");
      dot.style.cssText = `width:7px;height:7px;border-radius:50%;flex-shrink:0;transition:background .2s,transform .2s;
        background:${i === index ? "var(--add)" : "var(--border)"};
        transform:${i === index ? "scale(1.3)" : "scale(1)"};cursor:pointer`;
      dot.title = `Case #${String(PEO.getRowValue(PEO.state.preview.items[i], "# Case")).trim()}`;
      const ci = i;
      dot.addEventListener("click", () => PEO.renderPreviewAt(ci));
      dotsEl.appendChild(dot);
    }
    if (total > 12) {
      const lbl = document.createElement("span");
      lbl.style.cssText = "font-size:10px;color:var(--muted);margin-left:4px";
      lbl.textContent = `+${total - 12} more`;
      dotsEl.appendChild(lbl);
    }
  }

  // Botones: Next vs Generate CTA
  const nextBtn   = PEO.$("previewNextBtn");
  const genBtn    = PEO.$("previewGenerateBtn");
  const closeBtn2 = PEO.$("previewCloseBtn");
  const hint      = PEO.$("previewHint");

  if (isLast) {
    if (nextBtn)   { nextBtn.style.display   = "none"; }
    if (genBtn)    { genBtn.style.display    = ""; genBtn.textContent = `Generate all ${total} PDF${total > 1 ? "s" : ""} ↗`; }
    if (closeBtn2) { closeBtn2.style.display = ""; }
    if (hint)      hint.textContent = "You've reviewed all records. Generate PDFs below, or close to go back.";
  } else {
    if (nextBtn)   { nextBtn.style.display   = ""; nextBtn.textContent = `Next → (${total - index - 1} remaining)`; }
    if (genBtn)    { genBtn.style.display    = "none"; }
    if (closeBtn2) { closeBtn2.style.display = "none"; }
    if (hint)      hint.textContent = "Use ← → arrow keys to navigate · Esc to close · Edit record to adjust field values";
  }

  PEO.els.editCurrentPreviewBtn.onclick = () => PEO.openEditModal(row);

  if (genBtn) {
    genBtn.onclick = () => {
      PEO.closePreviewModal();
      PEO.generateState(PEO.state.preview._abbr, PEO.state.preview._proceso);
    };
  }
  if (closeBtn2) closeBtn2.onclick = PEO.closePreviewModal;
};

PEO.closePreviewModal = function() {
  PEO.els.previewModal.style.display = "none";
  if (PEO.state.preview.liveUrl) {
    URL.revokeObjectURL(PEO.state.preview.liveUrl);
    PEO.state.preview.liveUrl = "";
  }
  PEO.els.previewSingleFrame.src = "";
};
