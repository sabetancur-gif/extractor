/* global PEO */
/* generate.js — generación batch de PDFs y logging de KPI */
"use strict";

// ── KPI logging ────────────────────────────────────────────────────────────
PEO.logKpiEvent = function(action, o = {}) {
  PEO.state._kpiQueue.push({
    timestamp:    new Date().toISOString().slice(0, 19),
    username:     PEO.state.session.username,
    machine:      PEO.state.session.machine,
    action,
    state:        o.state        || "",
    process:      o.process      || "",
    case:         o.case         || "",
    file:         o.file         || "",
    duration_sec: o.duration_sec || 0,
  });
};

// ── Entry point: generate con pre-flight ───────────────────────────────────
PEO.generateState = async function(abbr, proceso) {
  try {
    const d = PEO.buildStateMap(PEO.state.currentRows)[abbr];
    if (!d) { PEO.notify("No data for " + abbr, "err"); return; }
    const rows = proceso === "ADD" ? d.adds : d.terms;
    if (!rows.length) { PEO.notify("Nothing pending", "err"); return; }
    const tf     = PEO.getTemplateFile(d.fullName, proceso);
    const tb     = await tf.arrayBuffer();
    const issues = await PEO.preflightValidate(rows, tb);
    if (issues.length) {
      PEO.showPreflightModal(issues, () => PEO.doGenerate(rows, tb, d.fullName, abbr, proceso));
      return;
    }
    await PEO.doGenerate(rows, tb, d.fullName, abbr, proceso);
  } catch(e) { PEO.notify(e.message, "err"); }
};

// ── Generación efectiva ────────────────────────────────────────────────────
PEO.doGenerate = async function(rows, templateBytes, stateName, abbr, proceso) {
  const t0    = Date.now();
  const today = new Date().toISOString().slice(0, 10);
  const total = rows.length;
  PEO.showProgress(`Generating ${abbr} ${proceso} PDFs`, total);

  if (PEO.state.outputDirHandle) {
    // Escritura silenciosa a carpeta de salida (File System Access API)
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const cv  = String(PEO.getRowValue(row, "# Case")).trim();
      const fn  = `${cv}-${proceso}-${abbr}-${today}.pdf`;
      PEO.updateProgress(i, total, fn);
      const bytes = await PEO.fillPdf(templateBytes, row, { flatten: true });
      const fh    = await PEO.state.outputDirHandle.getFileHandle(fn, { create: true });
      const w     = await fh.createWritable();
      await w.write(new Blob([bytes], { type: "application/pdf" }));
      await w.close();
      PEO.setRowValue(row, "Creado", "SI");
      PEO.logKpiEvent("GENERATE", {
        state: stateName, process: proceso, case: cv, file: fn,
        duration_sec: ((Date.now() - t0) / 1000).toFixed(2),
      });
    }
    PEO.hideProgress();
    PEO.refreshAll();
    PEO.notify(`Generated ${total} PDF(s) → output folder.`, "ok");

  } else {
    // ZIP descargable cuando no hay carpeta de salida configurada
    const entries = [];
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const cv  = String(PEO.getRowValue(row, "# Case")).trim();
      const fn  = `${cv}-${proceso}-${abbr}-${today}.pdf`;
      PEO.updateProgress(i, total, `Building ${fn}…`);
      const bytes = await PEO.fillPdf(templateBytes, row, { flatten: true });
      entries.push({ name: fn, data: new Uint8Array(bytes) });
      PEO.setRowValue(row, "Creado", "SI");
      PEO.logKpiEvent("GENERATE", {
        state: stateName, process: proceso, case: cv, file: fn,
        duration_sec: ((Date.now() - t0) / 1000).toFixed(2),
      });
    }
    PEO.updateProgress(total, total, "Bundling ZIP…");
    const zipName = `PEO-${abbr}-${proceso}-${today}.zip`;
    PEO.downloadZip(entries, zipName);
    PEO.hideProgress();
    PEO.refreshAll();
    PEO.notify(`Downloaded ${total} PDF(s) as ${zipName}.`, "ok");
  }
};
