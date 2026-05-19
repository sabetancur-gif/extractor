/* global PEO, XLSX */
/* state.js — estado global, referencias DOM y carga de archivos de configuración */
"use strict";

// ── Estado central de la aplicación ────────────────────────────────────────
PEO.state = {
  files:           new Map(),   // mapa de archivos cargados (key = ruta normalizada)
  workbookFile:    null,        // File del registros.xlsm
  workbook:        null,        // objeto XLSX parseado
  currentRows:     [],          // filas actuales del sheet Data
  selectedUser:    null,        // Nombre o elegido en pantalla de carga
  historicoFile:       null,   // File del historico_informe.xlsx si está en la carpeta cargada
  historicoCutoffDate: null,   // "YYYY-MM-DD" del modal de corte, o null = todo el histórico
  outputDirHandle: null,        // File System Access API — carpeta de salida
  outputDirLabel:  "",
  session:         { username: "—", machine: "—", lastImport: "—" },
  defaults:        { fields: {}, reportingDeadlineDays: 30 },
  validation:      null,        // contenido de report-validation.json
  selectedState:   null,        // abreviatura del estado seleccionado en el mapa
  preview: {
    items: [], index: 0, row: null,
    templateBytes: null, fieldTypes: new Map(), requiredFields: new Set(),
    liveUrl: "", renderToken: 0,
    _abbr: null, _proceso: null,
  },
  _kpiQueue: [],
};

// ── Shortcut $ + refs de elementos DOM ─────────────────────────────────────
PEO.$ = id => document.getElementById(id);

PEO.els = {
  get loadScreen()    { return PEO.$("loadScreen"); },
  get appBody()       { return PEO.$("appBody"); },
  get folderInput()   { return PEO.$("folderInput"); },
  get folderStatus()  { return PEO.$("folderStatus"); },
  get sessionUser()   { return PEO.$("sessionUser"); },
  get sessionImport() { return PEO.$("sessionImport"); },
  get alertsBanner()  { return PEO.$("alertsBanner"); },
  get alertsText()    { return PEO.$("alertsText"); },
  get notifyArea()    { return PEO.$("notifyArea"); },
  get kpiTotal()      { return PEO.$("kpiTotal"); },
  get kpiAdds()       { return PEO.$("kpiAdds"); },
  get kpiTerms()      { return PEO.$("kpiTerms"); },
  get kpiAlerts()     { return PEO.$("kpiAlerts"); },
  get kpiDone()       { return PEO.$("kpiDone"); },
  get kpiUrgent()     { return PEO.$("kpiUrgent"); },
  get stateGrid()     { return PEO.$("stateGrid"); },
  get detailCol()     { return PEO.$("detailCol"); },
  get previewModal()  { return PEO.$("previewModal"); },
  get previewSingleFrame()     { return PEO.$("previewSingleFrame"); },
  get previewPrevBtn()         { return PEO.$("previewPrevBtn"); },
  get previewNextBtn()         { return PEO.$("previewNextBtn"); },
  get previewCounter()         { return PEO.$("previewCounter"); },
  get previewCaseTitle()       { return PEO.$("previewCaseTitle"); },
  get editCurrentPreviewBtn()  { return PEO.$("editCurrentPreviewBtn"); },
  get editModalOverlay()       { return PEO.$("editModalOverlay"); },
  get editModalBody()          { return PEO.$("editModalBody"); },
  get btnPickOutput()          { return PEO.$("btnPickOutput"); },
  get btnSaveWorkbook()        { return PEO.$("btnSaveWorkbook"); },
  get btnEditDefaults()        { return PEO.$("btnEditDefaults"); },
  get defaultsModal()          { return PEO.$("defaultsModal"); },
};

// ── Carga de session.json (generado por Python) ─────────────────────────────
PEO.loadSession = async function() {
  const f = PEO.findFile("session.json"); if (!f) return;
  try {
    const s = JSON.parse(await f.text());
    PEO.state.session.username   = s.username   || "—";
    PEO.state.session.machine    = s.machine    || "—";
    PEO.state.session.lastImport = s.last_import
      ? s.last_import.replace("T", " ").slice(0, 16) : "—";
    PEO.els.sessionUser.textContent   = PEO.state.session.username;
    PEO.els.sessionImport.textContent = `Last import: ${PEO.state.session.lastImport}`;
  } catch { /* session opcional */ }
};

// ── Carga de defaults.json ──────────────────────────────────────────────────
PEO.loadDefaults = async function() {
  const f = PEO.findFile("defaults.json");
  if (!f) { PEO.notify("defaults.json not found — add it to use PEO-level pre-fills.", "info"); return; }
  try {
    const raw = JSON.parse(await f.text());
    PEO.state.defaults.fields                = raw.defaults || {};
    PEO.state.defaults.reportingDeadlineDays = raw.reporting_deadline_days || 30;
  } catch(e) { PEO.notify("defaults.json error: " + e.message, "err"); }
};

// ── Carga de report-validation.json (generado por Python) ──────────────────
PEO.loadValidationReport = async function() {
  const f = PEO.findFile("report-validation.json");
  if (!f) { PEO.state.validation = null; return; }
  try { PEO.state.validation = JSON.parse(await f.text()); }
  catch { PEO.state.validation = null; }
};

PEO.getTemplateAlert = (sn, pr) =>
  (PEO.state.validation?.alerts || []).find(
    a => PEO.norm(a.estado) === PEO.norm(sn) && PEO.norm(a.proceso) === PEO.norm(pr)
  ) || null;

PEO.hasAnyTemplateAlert = sn =>
  (PEO.state.validation?.alerts || []).some(a => PEO.norm(a.estado) === PEO.norm(sn));

// ── Lectura de filas del sheet Data ────────────────────────────────────────
PEO.readDataRows = function() {
  const ws = PEO.state.workbook?.Sheets?.[PEO.DATA_SHEET];
  if (!ws) throw new Error(`Sheet "${PEO.DATA_SHEET}" not found.`);
  return XLSX.utils.sheet_to_json(ws, { defval: "" });
};
