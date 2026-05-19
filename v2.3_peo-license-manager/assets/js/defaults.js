/* global PEO */
/* defaults.js — modal de edición de defaults.json */
"use strict";

PEO.openDefaultsModal = function() {
  const modal = PEO.els.defaultsModal; if (!modal) return;
  const body  = PEO.$("defaultsBody");  if (!body)  return;

  body.innerHTML = `
    <div class="preview-field">
      <label>Reporting deadline (days from effective date)</label>
      <input type="number" id="defDeadline" value="${PEO.state.defaults.reportingDeadlineDays}" min="1" max="365" style="width:80px">
    </div>
    <div style="margin:12px 0 6px;font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em">PEO-level field defaults</div>
    ${Object.entries(PEO.state.defaults.fields).map(([k, v]) => `
      <div class="preview-field">
        <label>${PEO.esc(k)}</label>
        <input type="text" class="def-field-input" data-key="${PEO.esc(k)}" value="${PEO.esc(String(v))}">
      </div>`).join("")}
    <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:8px">Add new field</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <input type="text" id="defNewKey" placeholder="PDF field name" style="flex:1;min-width:140px">
        <input type="text" id="defNewVal" placeholder="Value"          style="flex:1;min-width:140px">
        <button class="main-btn" id="defAddRowBtn">Add</button>
      </div>
    </div>`;

  PEO.$("defAddRowBtn").addEventListener("click", () => {
    const k = PEO.$("defNewKey").value.trim();
    const v = PEO.$("defNewVal").value.trim();
    if (!k) return;
    PEO.state.defaults.fields[k] = v;
    PEO.openDefaultsModal();
    PEO.notify(`Added default: ${k}`, "ok");
  });

  modal.classList.add("open");
};

PEO.saveDefaultsFromModal = function() {
  const dl = parseInt(PEO.$("defDeadline")?.value || "30", 10);
  PEO.state.defaults.reportingDeadlineDays = isNaN(dl) ? 30 : dl;
  document.querySelectorAll(".def-field-input").forEach(inp => {
    if (inp.dataset.key) PEO.state.defaults.fields[inp.dataset.key] = inp.value.trim();
  });
  PEO.els.defaultsModal.classList.remove("open");

  // Descarga el defaults.json actualizado
  const blob = new Blob([JSON.stringify({
    reporting_deadline_days: PEO.state.defaults.reportingDeadlineDays,
    defaults: PEO.state.defaults.fields,
  }, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a   = document.createElement("a");
  a.href = url; a.download = "defaults.json"; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1200);
  PEO.notify("Defaults saved — replace defaults.json in your project folder.", "ok");
};
