/* global PEO, XLSX */
/* report.js — informe PDF, Excel de sesión, histórico, modal de corte */
"use strict";

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 1 — Estadísticas de sesión
// ═══════════════════════════════════════════════════════════════════════════

PEO.buildSessionStats = function () {
  const events   = PEO.state._kpiQueue.filter(e => e.action === "GENERATE");
  const operator = PEO.state.selectedUser || PEO.state.session.username || "—";
  const now      = new Date();
  const byState  = {}, byProcess = { ADD: 0, TERM: 0 };

  for (const e of events) {
    const st = e.state || "Unknown", pr = e.process || "—";
    if (!byState[st]) byState[st] = { ADD: 0, TERM: 0, total: 0, totalSec: 0 };
    byState[st][pr]       = (byState[st][pr] || 0) + 1;
    byState[st].total++;
    byState[st].totalSec += parseFloat(e.duration_sec || 0);
    byProcess[pr]         = (byProcess[pr] || 0) + 1;
  }

  const totalSec   = events.reduce((s, e) => s + parseFloat(e.duration_sec || 0), 0);
  const avgSec     = events.length > 0 ? totalSec / events.length : 0;
  const timestamps = events.map(e => e.timestamp).filter(Boolean).sort();

  return {
    operator,
    date:         now.toISOString().slice(0, 10),
    datetime:     now.toISOString().slice(0, 16).replace("T", " "),
    totalForms:   events.length,
    byState, byProcess,
    stateCount:   Object.keys(byState).length,
    totalSec:     totalSec.toFixed(1),
    avgSec:       avgSec.toFixed(1),
    sessionStart: timestamps[0]                     || now.toISOString().slice(0, 19),
    sessionEnd:   timestamps[timestamps.length - 1] || now.toISOString().slice(0, 19),
  };
};

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 2 — Modal de fecha de corte para el histórico
// ═══════════════════════════════════════════════════════════════════════════

PEO.showHistoricoCutoffModal = function (filename) {
  return new Promise(resolve => {
    const today       = new Date().toISOString().slice(0, 10);
    const oneMonthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
    const ov = document.createElement("div");
    ov.className    = "modal-overlay open";
    ov.style.zIndex = "600";
    ov.innerHTML = `
      <div style="background:var(--surface);border-radius:14px;padding:30px 34px;
                  max-width:480px;width:90vw;display:flex;flex-direction:column;gap:18px;
                  border:1px solid var(--border);box-shadow:0 24px 60px rgba(0,0,0,.5)">
        <div style="display:flex;align-items:center;gap:14px">
          <div style="font-size:30px">📊</div>
          <div>
            <div style="font-size:15px;font-weight:800;color:var(--text)">Histórico encontrado</div>
            <code style="font-size:11px;color:var(--add)">${PEO.esc(filename)}</code>
          </div>
        </div>
        <div style="font-size:13px;color:var(--muted);line-height:1.7">
          ¿Desde qué fecha incluir la data previa en el informe?
        </div>
        <div style="display:flex;flex-direction:column;gap:6px">
          <label style="font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:.06em;color:var(--muted)">Incluir desde:</label>
          <input type="date" id="cutoffDateInput" value="${oneMonthAgo}" max="${today}"
                 style="padding:9px 12px;border:1px solid var(--border);border-radius:var(--radius);
                        background:var(--surface2);color:var(--text);font-size:13px;
                        font-family:inherit;width:100%">
          <div style="font-size:11px;color:var(--muted)">
            Vacío = <strong style="color:var(--text)">todo el histórico</strong>.
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="main-btn cta" id="cutoffConfirmBtn" style="flex:1">✓ Confirmar fecha</button>
          <button class="main-btn" id="cutoffAllBtn">↺ Todo</button>
          <button class="main-btn" id="cutoffIgnoreBtn">Ignorar</button>
        </div>
      </div>`;
    document.body.appendChild(ov);
    document.getElementById("cutoffConfirmBtn").addEventListener("click", () => {
      const val = document.getElementById("cutoffDateInput").value.trim();
      ov.remove(); resolve(val || null);
    });
    document.getElementById("cutoffAllBtn").addEventListener("click",  () => { ov.remove(); resolve(null); });
    document.getElementById("cutoffIgnoreBtn").addEventListener("click", () => {
      PEO.state.historicoFile = null; ov.remove(); resolve(undefined);
    });
  });
};

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 3 — SVG helpers
// ═══════════════════════════════════════════════════════════════════════════

function _svgBarChart(byState) {
  const entries = Object.entries(byState).sort((a, b) => b[1].total - a[1].total);
  if (!entries.length)
    return "<p style='color:#888;font-size:12px;padding:16px 0'>Sin formularios generados.</p>";

  const maxVal  = Math.max(...entries.map(([, v]) => v.total), 1);
  const BAR_W   = Math.max(28, Math.min(52, Math.floor(520 / entries.length) - 6));
  const GAP = 6, CHART_H = 180, LABEL_H = 22, PAD_L = 30;
  const totalW  = PAD_L + entries.length * (BAR_W + GAP) + 20;

  let bars = "";
  entries.forEach(([state, data], i) => {
    const x = PAD_L + i * (BAR_W + GAP);
    const addH  = Math.round((data.ADD  / maxVal) * (CHART_H - 30));
    const termH = Math.round((data.TERM / maxVal) * (CHART_H - 30));
    const totalH = addH + termH;
    const yBase  = CHART_H - LABEL_H;
    if (termH > 0)
      bars += `<rect x="${x}" y="${yBase-totalH}" width="${BAR_W}" height="${termH}"
                fill="#b45309" rx="3" opacity=".85"/>`;
    if (addH > 0)
      bars += `<rect x="${x}" y="${yBase-totalH+termH}" width="${BAR_W}" height="${addH}"
                fill="#2563eb" rx="3" opacity=".9"/>`;
    bars += `<text x="${x+BAR_W/2}" y="${yBase-totalH-5}" text-anchor="middle"
               font-size="10" font-weight="700" fill="#333">${data.total}</text>`;
    const lbl = state.length > 9 ? state.slice(0, 9) + "…" : state;
    bars += `<text x="${x+BAR_W/2}" y="${yBase+15}" text-anchor="middle"
               font-size="9" fill="#666">${lbl}</text>`;
  });

  const refs = [0.25, 0.5, 0.75, 1].map(pct => {
    const y = CHART_H - LABEL_H - Math.round(pct * (CHART_H - 30));
    const v = Math.round(pct * maxVal);
    return `<line x1="${PAD_L-4}" y1="${y}" x2="${totalW-4}" y2="${y}"
                  stroke="#e0e0e0" stroke-width="1" stroke-dasharray="3,3"/>
             <text x="${PAD_L-6}" y="${y+3}" text-anchor="end" font-size="8" fill="#bbb">${v}</text>`;
  }).join("");

  return `<svg width="${totalW}" height="${CHART_H+4}" xmlns="http://www.w3.org/2000/svg"
               style="overflow:visible">
    ${refs}${bars}
    <line x1="${PAD_L}" y1="0" x2="${PAD_L}" y2="${CHART_H-LABEL_H}" stroke="#ccc" stroke-width="1"/>
    <line x1="${PAD_L}" y1="${CHART_H-LABEL_H}" x2="${totalW-4}" y2="${CHART_H-LABEL_H}"
          stroke="#ccc" stroke-width="1"/>
  </svg>`;
}

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 4 — Informe PDF (sin información repetida + Yo vs Equipo)
// ═══════════════════════════════════════════════════════════════════════════

function _buildComparison(stats, historicoRows) {
  const me  = stats.operator.toLowerCase();
  const myH = historicoRows.filter(h => String(h.operador || "").trim().toLowerCase() === me);
  function avg(arr, field) {
    if (!arr.length) return null;
    return arr.reduce((s, h) => s + (Number(h[field]) || 0), 0) / arr.length;
  }
  function fmt(v, sfx = "") { return v === null ? "—" : Number(v).toFixed(1) + sfx; }
  function delta(session, ref, hib) {
    if (ref === null) return { html: "—", cls: "" };
    const d    = session - ref;
    const good = hib ? d >= 0 : d <= 0;
    const arr  = Math.abs(d) < 0.05 ? "→" : d > 0 ? "↑" : "↓";
    const sign = d >= 0 ? "+" : "";
    return {
      html: `${arr} ${sign}${Math.abs(d).toFixed(1)}`,
      cls:  Math.abs(d) < 0.05 ? "delta-neu" : good ? "delta-pos" : "delta-neg",
    };
  }
  const metrics = [
    { label:"Formularios",    session:stats.totalForms,          myAvg:avg(myH,"total_formularios"),  teamAvg:avg(historicoRows,"total_formularios"),  hib:true,  sfx:"" },
    { label:"ADDs",           session:stats.byProcess.ADD||0,    myAvg:avg(myH,"adds"),               teamAvg:avg(historicoRows,"adds"),               hib:true,  sfx:"" },
    { label:"TERMs",          session:stats.byProcess.TERM||0,   myAvg:avg(myH,"terms"),              teamAvg:avg(historicoRows,"terms"),              hib:true,  sfx:"" },
    { label:"Estados",        session:stats.stateCount,          myAvg:avg(myH,"estados"),            teamAvg:avg(historicoRows,"estados"),            hib:true,  sfx:"" },
    { label:"T. prom / form", session:parseFloat(stats.avgSec),  myAvg:avg(myH,"tiempo_promedio_seg"),teamAvg:avg(historicoRows,"tiempo_promedio_seg"),hib:false, sfx:"s"},
  ];
  return { metrics, mySessionCount: myH.length, teamSessionCount: historicoRows.length, fmt, delta };
}

PEO.generatePdfReport = function (stats, historicoRows = []) {
  const comp    = _buildComparison(stats, historicoRows);
  const hasComp = historicoRows.length > 0;
  const hist4   = historicoRows.slice(-4);
  const byState = stats.byState;
  const topState = Object.entries(byState).sort((a,b)=>b[1].total-a[1].total)[0]?.[0] || "—";
  const soloAdd  = Object.values(byState).filter(d=>d.ADD>0&&d.TERM===0).length;
  const soloTerm = Object.values(byState).filter(d=>d.TERM>0&&d.ADD===0).length;
  const both     = Object.values(byState).filter(d=>d.ADD>0&&d.TERM>0).length;

  // ── Tabla Yo vs Equipo ──────────────────────────────────────────────────
  const compRows = comp.metrics.map(m => {
    const dMy = comp.delta(m.session, m.myAvg, m.hib);
    return `<tr>
      <td class="cmp-lbl">${m.label}</td>
      <td class="cmp-val cmp-me">${m.session}${m.sfx}</td>
      <td class="cmp-val">${comp.fmt(m.myAvg, m.sfx)}</td>
      <td class="cmp-val">${comp.fmt(m.teamAvg, m.sfx)}</td>
      <td class="cmp-d ${dMy.cls}">${dMy.html}</td>
    </tr>`;
  }).join("");

  const compSection = hasComp ? `
    <div class="section">
      <h2 class="stitle"><div class="stitle-accent" style="background:#7c3aed"></div> Yo vs Equipo</h2>
      <div class="comp-meta">
        Basado en <strong>${comp.mySessionCount}</strong> sesión(es) tuyas y
        <strong>${comp.teamSessionCount}</strong> del equipo en el período seleccionado. &nbsp;
        <span style="color:#0369a1">↑ verde = mejor que tu media &nbsp;·&nbsp; ↓ rojo = por debajo</span>
      </div>
      <table class="dt comp-tbl">
        <thead><tr>
          <th>Métrica</th>
          <th style="color:#93c5fd">Esta Sesión</th>
          <th>Mi Promedio</th>
          <th>Prom. Equipo</th>
          <th>Δ vs Mi Media</th>
        </tr></thead>
        <tbody>${compRows}</tbody>
      </table>
    </div>` : "";

  // ── Histórico ───────────────────────────────────────────────────────────
  const historicoSection = hist4.length ? `
    <div class="section">
      <h2 class="stitle">
        <div class="stitle-accent" style="background:#0891b2"></div>
        Últimas ${hist4.length} sesiones del equipo
      </h2>
      <table class="dt">
        <thead><tr>
          <th>Fecha</th><th>Operador</th><th>Forms</th>
          <th>ADD</th><th>TERM</th><th>Estados</th><th>T. Prom.</th>
        </tr></thead>
        <tbody>${hist4.map((h,i) => `<tr class="${i%2?"even":""}">
          <td class="td-l">${PEO.esc(String(h.fecha_realizacion||"").slice(0,16))}</td>
          <td class="td-l" style="${String(h.operador||"").toLowerCase()===stats.operator.toLowerCase()?"font-weight:800;color:#2563eb":""}">${PEO.esc(String(h.operador||"—"))}</td>
          <td class="td-c fw7">${h.total_formularios||0}</td>
          <td class="td-c"><span class="ba">${h.adds||0}</span></td>
          <td class="td-c"><span class="bt">${h.terms||0}</span></td>
          <td class="td-c">${h.estados||0}</td>
          <td class="td-c mu">${h.tiempo_promedio_seg?Number(h.tiempo_promedio_seg).toFixed(1)+"s":"—"}</td>
        </tr>`).join("")}</tbody>
      </table>
      <div style="font-size:10px;color:#9ca3af;margin-top:5px">
        Tu nombre en azul · Período: desde ${PEO.state.historicoCutoffDate || "inicio del histórico"}
      </div>
    </div>` : `
    <div class="section">
      <h2 class="stitle">
        <div class="stitle-accent" style="background:#0891b2"></div> Histórico
      </h2>
      <p style="font-size:12px;color:#9ca3af;padding:10px 0">
        Sin sesiones anteriores en el período.<br>
        Carga <code>historico_informe.xlsx</code> en la carpeta para ver comparaciones.
      </p>
    </div>`;

  const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Informe PEO · ${PEO.esc(stats.operator)} · ${stats.date}</title>
<style>
  @page { margin:15mm 13mm; size:A4; }
  *,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:'Segoe UI',system-ui,Arial,sans-serif; color:#111827;
         background:#fff; font-size:13px; line-height:1.55; }

  .pbar { background:#111827; color:#f3f4f6; padding:10px 36px;
          display:flex; justify-content:space-between; align-items:center; font-size:12px; }
  .pbar button { background:#2563eb; color:#fff; border:none; padding:7px 22px;
                 border-radius:6px; font-size:12px; font-weight:700;
                 cursor:pointer; font-family:inherit; }
  .pbar button:hover { background:#1d4ed8; }
  @media print { .pbar{display:none;} body{-webkit-print-color-adjust:exact;print-color-adjust:exact;} }

  .hdr { background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 45%,#1d4ed8 100%);
         color:#fff; padding:28px 36px 24px; display:flex;
         justify-content:space-between; align-items:flex-start; gap:24px; }
  .hdr-badge { display:inline-block; background:rgba(255,255,255,.15);
               border:1px solid rgba(255,255,255,.25); border-radius:20px;
               padding:3px 12px; font-size:10px; font-weight:700;
               text-transform:uppercase; letter-spacing:.08em; margin-bottom:8px; }
  .hdr-title  { font-size:22px; font-weight:800; letter-spacing:-.5px; }
  .hdr-sub    { font-size:12px; color:rgba(255,255,255,.55); margin-top:4px; }
  .hdr-op     { font-size:22px; font-weight:800; color:#93c5fd; text-align:right; }
  .hdr-detail { font-size:11px; color:rgba(255,255,255,.6); margin-top:5px;
                line-height:2.1; text-align:right; }

  /* KPI — 4 cards únicos (sin repetir lo de la gráfica ni el tiempo dos veces) */
  .kpis { display:grid; grid-template-columns:repeat(4,1fr);
          background:#f9fafb; border-bottom:1px solid #e5e7eb; }
  .kc   { padding:18px 10px; text-align:center; border-right:1px solid #e5e7eb; }
  .kc:last-child { border-right:none; }
  .kv   { font-size:28px; font-weight:800; line-height:1.1; }
  .kl   { font-size:10px; color:#9ca3af; text-transform:uppercase; letter-spacing:.06em; margin-top:3px; }
  .ks   { font-size:11px; font-weight:700; padding:2px 10px; border-radius:12px;
          margin-top:5px; display:inline-block; }
  .ks-a { background:#dbeafe; color:#1d4ed8; }
  .ks-t { background:#fef3c7; color:#b45309; }
  .c-dk { color:#111827; } .c-bl { color:#2563eb; }

  .body  { padding:26px 36px; display:flex; flex-direction:column; gap:26px; }
  .stitle { font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.1em;
            color:#6b7280; padding-bottom:8px; margin-bottom:14px;
            border-bottom:2px solid #e5e7eb; display:flex; align-items:center; gap:8px; }
  .stitle-accent { width:16px; height:3px; border-radius:2px; flex-shrink:0; }

  /* Gráfica + sidebar */
  .viz-row  { display:flex; gap:24px; align-items:flex-start; }
  .viz-main { flex:1; min-width:0; }
  .viz-side { width:140px; flex-shrink:0; display:flex; flex-direction:column; gap:9px; }
  .stat-card { background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px;
               padding:11px 13px; border-left:3px solid #2563eb; }
  .stat-card.v { border-left-color:#7c3aed; }
  .stat-card.g { border-left-color:#16a34a; }
  .stat-card.o { border-left-color:#ea580c; }
  .stat-lbl { font-size:10px; color:#9ca3af; text-transform:uppercase; letter-spacing:.05em; }
  .stat-val { font-size:18px; font-weight:800; color:#111827; margin-top:2px; }
  .leg { display:flex; gap:12px; margin-top:8px; flex-wrap:wrap; }
  .li  { display:flex; align-items:center; gap:5px; font-size:11px; color:#6b7280; }
  .ld  { width:10px; height:10px; border-radius:2px; flex-shrink:0; }

  /* Tablas */
  .dt          { width:100%; border-collapse:collapse; font-size:12px; }
  .dt thead tr { background:#111827; color:#fff; }
  .dt thead th { padding:9px 12px; text-align:left; font-size:10px;
                 text-transform:uppercase; letter-spacing:.05em; font-weight:700; }
  .dt tbody tr:nth-child(even),.dt tbody tr.even { background:#f9fafb; }
  .td-l { padding:8px 12px; font-weight:600; }
  .td-c { padding:8px 12px; text-align:center; }
  .fw7  { font-weight:700; } .mu { color:#9ca3af; }
  .ba { background:#dbeafe; color:#1d4ed8; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
  .bt { background:#fef3c7; color:#b45309;  padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }

  /* Yo vs Equipo */
  .comp-meta { font-size:11px; color:#374151; background:#f0f9ff;
               border:1px solid #bae6fd; border-radius:6px; padding:8px 12px; margin-bottom:12px; }
  .comp-meta strong { color:#0369a1; }
  .comp-tbl thead tr { background:#1e3a5f; }
  .cmp-lbl { padding:9px 12px; font-weight:600; }
  .cmp-val { padding:9px 12px; text-align:center; color:#374151; }
  .cmp-me  { font-weight:800; color:#2563eb; background:#eff6ff; }
  .cmp-d   { padding:9px 12px; text-align:center; font-size:11px; font-weight:700; }
  .delta-pos { color:#15803d; } .delta-neg { color:#b91c1c; } .delta-neu { color:#9ca3af; }

  .ftr { margin-top:4px; padding:11px 36px; background:#f9fafb;
         border-top:1px solid #e5e7eb; display:flex;
         justify-content:space-between; font-size:10px; color:#9ca3af; }
</style>
</head>
<body>

<div class="pbar">
  <span>⚖ PEO License Manager &nbsp;·&nbsp; Informe de Sesión &nbsp;·&nbsp; ${PEO.esc(stats.operator)}</span>
  <button onclick="window.print()">⬇ Guardar como PDF</button>
</div>

<div class="hdr">
  <div>
    <div class="hdr-badge">Informe de Sesión</div>
    <div class="hdr-title">⚖ PEO License Manager</div>
    <div class="hdr-sub">Actividad del operador · ${stats.datetime}</div>
  </div>
  <div>
    <div class="hdr-op">${PEO.esc(stats.operator)}</div>
    <div class="hdr-detail">
      Sesión: ${stats.sessionStart.slice(11,16)} → ${stats.sessionEnd.slice(11,16)}<br>
      ${stats.datetime}
    </div>
  </div>
</div>

<div class="kpis">
  <div class="kc">
    <div class="kv c-dk">${stats.totalForms}</div>
    <div class="kl">Total Formularios</div>
    <div class="ks ks-a">ADD ${stats.byProcess.ADD||0}</div>
  </div>
  <div class="kc">
    <div class="kv c-dk">${stats.stateCount}</div>
    <div class="kl">Estados Cubiertos</div>
    <div class="ks ks-t">TERM ${stats.byProcess.TERM||0}</div>
  </div>
  <div class="kc">
    <div class="kv c-bl">${stats.avgSec}s</div>
    <div class="kl">T. Promedio / Form</div>
  </div>
  <div class="kc">
    <div class="kv c-dk">${stats.totalSec}s</div>
    <div class="kl">Tiempo Total Sesión</div>
  </div>
</div>

<div class="body">

  <div class="section">
    <h2 class="stitle">
      <div class="stitle-accent" style="background:#2563eb"></div>
      Distribución de Formularios por Estado
    </h2>
    <div class="viz-row">
      <div class="viz-main">
        ${_svgBarChart(stats.byState)}
        <div class="leg">
          <div class="li"><div class="ld" style="background:#2563eb"></div>ADD</div>
          <div class="li"><div class="ld" style="background:#b45309"></div>TERM</div>
        </div>
      </div>
      <div class="viz-side">
        <div class="stat-card">
          <div class="stat-lbl">Top estado</div>
          <div class="stat-val" style="font-size:14px">${topState}</div>
        </div>
        <div class="stat-card v">
          <div class="stat-lbl">Solo ADD</div>
          <div class="stat-val c-bl">${soloAdd}</div>
        </div>
        <div class="stat-card g">
          <div class="stat-lbl">Solo TERM</div>
          <div class="stat-val">${soloTerm}</div>
        </div>
        <div class="stat-card o">
          <div class="stat-lbl">ADD + TERM</div>
          <div class="stat-val">${both}</div>
        </div>
      </div>
    </div>
  </div>

  ${compSection}
  ${historicoSection}

</div>

<div class="ftr">
  <span>PEO License Manager · Generado automáticamente · ${stats.datetime}</span>
  <span>Operador: ${PEO.esc(stats.operator)} · ${stats.totalForms} formulario(s)</span>
</div>

</body>
</html>`;

  const blob = new Blob([html], { type:"text/html;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const win  = window.open(url, "_blank");
  if (!win) PEO.notify("Habilita ventanas emergentes para ver el informe PDF.", "err");
  setTimeout(() => URL.revokeObjectURL(url), 15000);
};

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 5 — Histórico Excel acumulado
// ═══════════════════════════════════════════════════════════════════════════

async function _readHistoricoRows(cutoffDate) {
  const hf = PEO.state.historicoFile;
  if (!hf) return [];
  try {
    const wb   = XLSX.read(await hf.arrayBuffer(), { type: "array" });
    const ws   = wb.Sheets[wb.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });
    if (!cutoffDate) return rows;
    return rows.filter(r => String(r.fecha_realizacion || "").slice(0, 10) >= cutoffDate);
  } catch (e) {
    PEO.notify("Error leyendo histórico: " + e.message, "err");
    return [];
  }
}

PEO.buildHistorico = async function (stats) {
  const existingRows = await _readHistoricoRows(PEO.state.historicoCutoffDate);
  const estadosStr   = Object.entries(stats.byState).map(([s,d])=>`${s}:${d.total}`).join(" | ");
  const newRow = {
    fecha_realizacion:   stats.datetime,
    operador:            stats.operator,
    total_formularios:   stats.totalForms,
    adds:                stats.byProcess.ADD  || 0,
    terms:               stats.byProcess.TERM || 0,
    estados:             stats.stateCount,
    detalle_estados:     estadosStr,
    tiempo_total_seg:    parseFloat(stats.totalSec),
    tiempo_promedio_seg: parseFloat(stats.avgSec),
    hora_inicio:         stats.sessionStart.slice(11, 16),
    hora_fin:            stats.sessionEnd.slice(11, 16),
  };
  const allRows = [...existingRows, newRow];

  const wb     = XLSX.utils.book_new();
  const wsHist = XLSX.utils.json_to_sheet(allRows);
  wsHist["!cols"] = [{wch:18},{wch:12},{wch:17},{wch:7},{wch:7},{wch:8},{wch:42},{wch:16},{wch:18},{wch:11},{wch:9}];
  XLSX.utils.book_append_sheet(wb, wsHist, "Histórico");

  const byOp = {};
  for (const r of allRows) {
    const op = r.operador || "—";
    if (!byOp[op]) byOp[op] = { operador:op, sesiones:0, total_formularios:0, adds:0, terms:0, tiempo_total_seg:0, estados_set:new Set() };
    byOp[op].sesiones++;
    byOp[op].total_formularios += Number(r.total_formularios)||0;
    byOp[op].adds              += Number(r.adds)||0;
    byOp[op].terms             += Number(r.terms)||0;
    byOp[op].tiempo_total_seg  += Number(r.tiempo_total_seg)||0;
    String(r.detalle_estados||"").split(" | ").forEach(s=>{if(s.includes(":"))byOp[op].estados_set.add(s.split(":")[0]);});
  }
  const summaryRows = Object.values(byOp).map(o => ({
    operador:             o.operador,
    sesiones:             o.sesiones,
    total_formularios:    o.total_formularios,
    adds:                 o.adds,
    terms:                o.terms,
    promedio_por_sesion:  o.sesiones>0?(o.total_formularios/o.sesiones).toFixed(1):0,
    estados_cubiertos:    o.estados_set.size,
    tiempo_total_seg:     o.tiempo_total_seg.toFixed(1),
    tiempo_promedio_form: o.total_formularios>0?(o.tiempo_total_seg/o.total_formularios).toFixed(1):0,
  }));
  const wsSum = XLSX.utils.json_to_sheet(summaryRows);
  wsSum["!cols"] = [{wch:12},{wch:9},{wch:17},{wch:7},{wch:7},{wch:18},{wch:16},{wch:15},{wch:18}];
  XLSX.utils.book_append_sheet(wb, wsSum, "Por Operador");

  const buf  = XLSX.write(wb, { bookType:"xlsx", type:"array" });
  const blob = new Blob([buf], { type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url; a.download = "historico_informe.xlsx"; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  PEO.notify(`Histórico: ${allRows.length} sesión(es) acumuladas.`, "ok");
};

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 6 — Excel de sesión (tabla limpia de formularios generados)
// ═══════════════════════════════════════════════════════════════════════════

PEO.buildSessionExcel = function (stats) {
  const events      = PEO.state._kpiQueue.filter(e => e.action === "GENERATE");
  const outputLabel = PEO.state.outputDirLabel || "ZIP descargado";

  const rows = events.map(e => ({
    fecha_generacion: String(e.timestamp || stats.datetime).slice(0, 16).replace("T", " "),
    operador:         e.username  || stats.operator,
    estado:           e.state     || "—",
    proceso:          e.process   || "—",
    "# case":         e.case      || "—",
    archivo_pdf:      e.file      || "—",
    ruta_carpeta:     outputLabel,
    duracion_seg:     parseFloat(e.duration_sec || 0).toFixed(1),
  }));

  const wb  = XLSX.utils.book_new();
  const ws1 = XLSX.utils.json_to_sheet(rows.length ? rows : [{
    fecha_generacion:"—", operador:"—", estado:"—", proceso:"—",
    "# case":"—", archivo_pdf:"—", ruta_carpeta:"—", duracion_seg:"—",
  }]);
  ws1["!cols"] = [{wch:18},{wch:12},{wch:18},{wch:8},{wch:16},{wch:38},{wch:34},{wch:12}];
  XLSX.utils.book_append_sheet(wb, ws1, "Formularios Generados");

  const summary = [
    { metrica:"Operador",                     valor: stats.operator },
    { metrica:"Fecha y hora",                 valor: stats.datetime },
    { metrica:"Inicio sesión",                valor: stats.sessionStart.slice(11, 16) },
    { metrica:"Fin sesión",                   valor: stats.sessionEnd.slice(11, 16) },
    { metrica:"Total formularios generados",  valor: stats.totalForms },
    { metrica:"ADDs",                         valor: stats.byProcess.ADD  || 0 },
    { metrica:"TERMs",                        valor: stats.byProcess.TERM || 0 },
    { metrica:"Estados cubiertos",            valor: stats.stateCount },
    { metrica:"Tiempo total (seg)",           valor: parseFloat(stats.totalSec) },
    { metrica:"Tiempo promedio / form (seg)", valor: parseFloat(stats.avgSec) },
    { metrica:"Carpeta de salida",            valor: outputLabel },
  ];
  const ws2 = XLSX.utils.json_to_sheet(summary);
  ws2["!cols"] = [{wch:38},{wch:22}];
  XLSX.utils.book_append_sheet(wb, ws2, "Resumen Sesión");

  const fname = `reporte_sesion_${stats.operator}_${stats.date}.xlsx`;
  const buf   = XLSX.write(wb, { bookType:"xlsx", type:"array" });
  const blob  = new Blob([buf], { type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement("a");
  a.href = url; a.download = fname; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  PEO.notify(`Reporte de sesión: ${fname}`, "ok");
};

// ═══════════════════════════════════════════════════════════════════════════
//  SECCIÓN 7 — Coordinador principal
// ═══════════════════════════════════════════════════════════════════════════

PEO.generateAllReports = async function () {
    const generated = PEO.state._kpiQueue.filter(e => e.action === "GENERATE");
    if (!generated.length) {
        PEO.notify("No hay formularios generados en esta sesión — sin datos para el informe.", "info");
        return;
    }

    PEO.notify("Generando informes de sesión…", "info");
    const stats    = PEO.buildSessionStats();
    const histRows = await _readHistoricoRows(PEO.state.historicoCutoffDate);

    // Excel de sesión — tabla limpia: estado, proceso, # case, carpeta
    PEO.buildSessionExcel(stats);

    // Informe PDF — abre en pestaña nueva → Ctrl+P para guardar como PDF
    await new Promise(r => setTimeout(r, 300));
    PEO.generatePdfReport(stats, histRows);

    // Histórico acumulado — actualiza y descarga historico_informe.xlsx
    await PEO.buildHistorico(stats);
};
