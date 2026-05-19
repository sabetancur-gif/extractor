/* global PEO */
/* utils.js — funciones utilitarias puras (sin side effects de DOM) */
"use strict";

// ── String helpers ──────────────────────────────────────────────────────────
PEO.norm = v => String(v ?? "").trim().toLowerCase().replace(/\s+/g, "_").replace(/\\/g, "/");
PEO.esc  = s => String(s ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;")
                                .replaceAll(">","&gt;").replaceAll('"',"&quot;");

PEO.fileKey   = f  => PEO.norm(f.webkitRelativePath || f.name);
PEO.isCreated = v  => ["si","sí","yes","true","1","x","creado"].includes(String(v ?? "").trim().toLowerCase());
PEO.debounce  = (fn, ms = 200) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
PEO.nameToAbbr = name => PEO.NAME_TO_ABBR[String(name || "").trim().toLowerCase()] || null;

// ── Búsqueda de archivo en el mapa de archivos cargados ────────────────────
PEO.findFile = function(suffix) {
  const w = PEO.norm(suffix);
  for (const [k, f] of PEO.state.files) if (k.endsWith(w)) return f;
  return null;
};

// ── Helpers de fila de Excel ───────────────────────────────────────────────
PEO.getRowValue = function(row, header) {
  const w = PEO.norm(header);
  const k = Object.keys(row).find(k => PEO.norm(k) === w);
  return k !== undefined ? row[k] : "";
};

PEO.setRowValue = function(row, header, value) {
  const w = PEO.norm(header);
  const k = Object.keys(row).find(k => PEO.norm(k) === w);
  if (k !== undefined) row[k] = value; else row[header] = value;
};

// Retorna [valor resuelto, fuente: "row" | "default" | "empty"]
PEO.getEffectiveValue = function(row, fieldNorm) {
  const rk = Object.keys(row).find(k => PEO.norm(k) === fieldNorm);
  const rv = rk !== undefined ? String(row[rk] ?? "").trim() : "";
  if (rv) return [rv, "row"];
  const dk = Object.keys(PEO.state.defaults.fields).find(k => PEO.norm(k) === fieldNorm);
  if (dk) { const dv = String(PEO.state.defaults.fields[dk] ?? "").trim(); if (dv) return [dv, "default"]; }
  return ["", "empty"];
};

// ── Fecha y deadline ───────────────────────────────────────────────────────
PEO.parseRowDate = function(row) {
  for (const c of PEO.DATE_CANDIDATES) {
    const v = String(PEO.getRowValue(row, c) || "").trim();
    if (!v) continue;
    let d = new Date(v);
    if (!isNaN(d.getTime())) return d;
    const m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (m) return new Date(`${m[3]}-${m[1].padStart(2,"0")}-${m[2].padStart(2,"0")}`);
  }
  return null;
};

PEO.daysUntilDeadline = function(row) {
  const d = PEO.parseRowDate(row);
  if (!d) return null;
  const dl = new Date(d);
  dl.setDate(dl.getDate() + PEO.state.defaults.reportingDeadlineDays);
  const today = new Date(); today.setHours(0,0,0,0); dl.setHours(0,0,0,0);
  return Math.floor((dl - today) / 86400000);
};

PEO.deadlineBadge = function(days) {
  if (days === null) return "";
  if (days < 0)  return `<span class="badge badge-alert">⚠ ${Math.abs(days)}d overdue</span>`;
  if (days <= 7) return `<span class="badge badge-term">⏰ ${days}d left</span>`;
  return `<span class="badge badge-gray">${days}d left</span>`;
};

// ── Notificaciones ─────────────────────────────────────────────────────────
PEO.notify = function(msg, kind = "info") {
  const p = document.createElement("div");
  p.className = `notify-pill ${kind}`;
  p.textContent = msg;
  PEO.els.notifyArea.appendChild(p);
  setTimeout(() => p.remove(), 4500);
};
