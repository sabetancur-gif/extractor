/* global PEO, XLSX */
/* workbook.js — guardado del workbook y refresh de la UI */
"use strict";

// ── Guardar registros.xlsm (actualiza Creado:SI) + genera informes de sesión
PEO.saveWorkbookToDisk = async function() {
  if (!PEO.state.workbook) { PEO.notify("No workbook loaded.", "err"); return; }

  // Actualizar la hoja Data con los flags Creado:SI en memoria
  const headers = Object.keys(PEO.state.currentRows[0] || {});
  const out     = [headers, ...PEO.state.currentRows.map(r => headers.map(h => r[h] ?? ""))];
  PEO.state.workbook.Sheets[PEO.DATA_SHEET] = XLSX.utils.aoa_to_sheet(out);

  const blob = new Blob(
    [XLSX.write(PEO.state.workbook, { bookType: "xlsm", type: "array" })],
    { type: "application/vnd.ms-excel.sheet.macroenabled.12" }
  );

  // Guardar registros.xlsm — necesario para persistir Creado:SI entre sesiones
  let saved = false;
  if ("showSaveFilePicker" in window) {
    try {
      const h = await window.showSaveFilePicker({
        suggestedName: "registros.xlsm",
        types: [{ description: "Excel Macro-Enabled",
                  accept: { "application/vnd.ms-excel.sheet.macroenabled.12": [".xlsm"] } }],
      });
      const w = await h.createWritable();
      await w.write(blob);
      await w.close();
      saved = true;
    } catch { return; }
  } else {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement("a");
    a.href = url; a.download = "registros.xlsm"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1200);
    saved = true;
  }

  if (!saved) return;

  PEO.logKpiEvent("SAVE_WORKBOOK");

  // Flash del botón
  const sb = PEO.$("btnSaveWorkbook");
  if (sb) {
    const orig = sb.textContent;
    sb.textContent      = "✓ Guardado — generando informes…";
    sb.style.background = "var(--done)";
    sb.style.color      = "#fff";
    setTimeout(() => {
      sb.textContent      = orig;
      sb.style.background = "";
      sb.style.color      = "";
    }, 3000);
  }

  // Generar: reporte_sesion.xlsx + PDF report + historico_informe.xlsx
  setTimeout(() => PEO.generateAllReports(), 400);
};

// ── Refresh completo de KPI + mapa + detalle ───────────────────────────────
PEO.refreshAll = function() {
  PEO.state.currentRows = PEO.readDataRows();
  const sm = PEO.buildStateMap(PEO.state.currentRows);
  PEO.updateKPIBar(sm);
  PEO.buildTileMap(sm);
  if (PEO.state.selectedState && sm[PEO.state.selectedState]) {
    PEO.renderDetail(PEO.state.selectedState, sm[PEO.state.selectedState]);
    document.querySelectorAll(".state-tile").forEach(el => {
      if (el.dataset.abbr === PEO.state.selectedState) el.classList.add("sel");
    });
  } else {
    PEO.renderDetailEmpty();
  }
};

// ── Carga de carpeta / archivos seleccionados ──────────────────────────────
PEO.loadFolder = async function(files) {
  PEO.state.files.clear();
  PEO.state.workbookFile  = null;
  PEO.state.currentRows   = [];
  PEO.state.selectedState = null;
  if (PEO.state.preview.liveUrl) URL.revokeObjectURL(PEO.state.preview.liveUrl);

  for (const f of files) {
    PEO.state.files.set(PEO.fileKey(f), f);
    if (/registros\.(xlsm|xlsx)$/i.test(f.name)) PEO.state.workbookFile = f;
    if (/historico_informe\.xlsx$/i.test(f.name)) PEO.state.historicoFile = f;
  }
  if (!PEO.state.workbookFile) throw new Error("registros.xlsm not found in the selected folder.");

  const loadErr = PEO.$("loadError");
  if (loadErr) { loadErr.style.color = "var(--add)"; loadErr.style.display = "block"; loadErr.textContent = "Reading workbook…"; }
  await new Promise(r => setTimeout(r, 30)); // allow paint

  PEO.state.workbook = XLSX.read(await PEO.state.workbookFile.arrayBuffer(), { type: "array" });
  if (loadErr) loadErr.textContent = "Loading session…";
  PEO.state.currentRows = PEO.readDataRows();

  await PEO.loadSession();

  // El operador elegido en pantalla de carga tiene prioridad sobre session.json
  if (PEO.state.selectedUser) {
    PEO.state.session.username = PEO.state.selectedUser;
    if (PEO.els.sessionUser) PEO.els.sessionUser.textContent = PEO.state.selectedUser;
  }
  await PEO.loadValidationReport();
  await PEO.loadDefaults();

  // Si existe historico_informe.xlsx en la carpeta, preguntar fecha de corte
  if (PEO.state.historicoFile) {
    if (loadErr) { loadErr.textContent = "Histórico encontrado…"; }
    PEO.state.historicoCutoffDate = await PEO.showHistoricoCutoffModal(
      PEO.state.historicoFile.name
    );
  }

  if (loadErr) loadErr.style.display = "none";

  const sm = PEO.buildStateMap(PEO.state.currentRows);
  PEO.updateKPIBar(sm);
  PEO.buildTileMap(sm);
  PEO.renderDetailEmpty();

  PEO.els.loadScreen.classList.add("hidden");
  PEO.els.appBody.classList.remove("hidden");
  PEO.notify(`Folder loaded — ${files.length} file(s).`, "ok");
  document.dispatchEvent(new CustomEvent("peo-folder-loaded"));
  PEO.els.folderStatus.textContent = `${files.length} files · ${PEO.state.session.username}`;
};
