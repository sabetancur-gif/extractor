/* global PEO */
/* map.js — construcción del mapa de estados, KPI bar y panel de detalle */
"use strict";

// ── Construcción del mapa de estados desde las filas Excel ─────────────────
PEO.buildStateMap = function(rows) {
  const map = {};
  for (const row of rows) {
    const fullName = String(PEO.getRowValue(row, "Estado") || "").trim();
    const proceso  = String(PEO.getRowValue(row, "Proceso") || "").trim().toUpperCase();
    const abbr     = PEO.nameToAbbr(fullName);
    if (!abbr || !["ADD", "TERM"].includes(proceso)) continue;
    if (!map[abbr]) map[abbr] = {
      fullName, adds: [], terms: [], addsDone: 0, termsDone: 0,
      minDaysLeft: null, hasOverdue: false, hasUrgent: false,
    };
    const created = PEO.isCreated(PEO.getRowValue(row, "Creado"));
    const days    = PEO.daysUntilDeadline(row);
    if (proceso === "ADD") {
      if (!created) { map[abbr].adds.push(row);  _trackDeadline(map[abbr], days); }
      else map[abbr].addsDone++;
    } else {
      if (!created) { map[abbr].terms.push(row); _trackDeadline(map[abbr], days); }
      else map[abbr].termsDone++;
    }
  }
  return map;
};

function _trackDeadline(e, days) {
  if (days === null) return;
  if (e.minDaysLeft === null || days < e.minDaysLeft) e.minDaysLeft = days;
  if (days < 0)  e.hasOverdue = true;
  if (days <= 7) e.hasUrgent  = true;
}

// ── KPI bar ────────────────────────────────────────────────────────────────
PEO.updateKPIBar = function(stateMap) {
  let adds = 0, terms = 0, done = 0, alerts = 0, urgent = 0;
  for (const d of Object.values(stateMap)) {
    adds  += d.adds.length;
    terms += d.terms.length;
    done  += d.addsDone + d.termsDone;
    if (PEO.hasAnyTemplateAlert(d.fullName)) alerts++;
    if (d.hasOverdue || d.hasUrgent) urgent++;
  }
  PEO.els.kpiTotal.textContent  = adds + terms;
  PEO.els.kpiAdds.textContent   = adds;
  PEO.els.kpiTerms.textContent  = terms;
  PEO.els.kpiAlerts.textContent = alerts;
  PEO.els.kpiDone.textContent   = done;
  if (PEO.els.kpiUrgent) PEO.els.kpiUrgent.textContent = urgent;

  if (alerts > 0) {
    PEO.els.alertsBanner.classList.remove("hidden");
    PEO.els.alertsText.textContent =
      `${alerts} state${alerts > 1 ? "s have" : " has"} template alerts — review before generating.`;
  } else {
    PEO.els.alertsBanner.classList.add("hidden");
  }
};

// ── Tile map (grid de estados) ─────────────────────────────────────────────
PEO.buildTileMap = function(stateMap) {
  PEO.els.stateGrid.innerHTML = "";
  for (const [abbr, [row, col]] of Object.entries(PEO.TILE_GRID)) {
    const d  = stateMap[abbr];
    const pa = d?.adds.length  || 0;
    const pt = d?.terms.length || 0;
    let status = "none";
    if (d && (pa || pt))               status = pa && pt ? "both" : pa ? "add" : "term";
    else if (d && (d.addsDone + d.termsDone) > 0) status = "done";

    let cls = "state-tile";
    if (status !== "none") cls += ` st-${status}`;
    if (d?.hasOverdue) cls += " st-overdue";
    else if (d?.hasUrgent) cls += " st-urgent";

    const tile = document.createElement("div");
    tile.className   = cls;
    tile.style.gridRow    = row + 1;
    tile.style.gridColumn = col + 1;
    tile.textContent  = abbr;
    tile.dataset.abbr = abbr;

    const tip = d?.minDaysLeft !== null && d?.minDaysLeft !== undefined
      ? (d.minDaysLeft < 0 ? ` — OVERDUE ${Math.abs(d.minDaysLeft)}d` : ` — ${d.minDaysLeft}d left`)
      : "";
    tile.title = (d ? d.fullName : PEO.ABBR_TO_NAME[abbr] || abbr) + tip;

    if (d && PEO.hasAnyTemplateAlert(d.fullName)) {
      const dot = document.createElement("div"); dot.className = "tile-alert-dot"; tile.appendChild(dot);
    }
    if (d?.hasOverdue) {
      const dot = document.createElement("div"); dot.className = "tile-deadline-dot"; tile.appendChild(dot);
    }

    tile.addEventListener("click", () => PEO.clickTile(abbr, tile, stateMap));
    PEO.els.stateGrid.appendChild(tile);
  }
};

PEO.clickTile = function(abbr, tileEl, stateMap) {
  document.querySelectorAll(".state-tile.sel").forEach(e => e.classList.remove("sel"));
  if (PEO.state.selectedState === abbr) {
    PEO.state.selectedState = null;
    PEO.renderDetailEmpty();
    return;
  }
  PEO.state.selectedState = abbr;
  tileEl.classList.add("sel");
  PEO.renderDetail(abbr, stateMap[abbr]);
};

// ── Panel de detalle ────────────────────────────────────────────────────────
PEO.renderDetailEmpty = function() {
  PEO.els.detailCol.innerHTML = `
    <div class="panel detail-empty">
      <div class="detail-empty-icon">🗺</div>
      <div>Select a state on the map<br>to view pending filings.</div>
    </div>`;
};

PEO.renderDetail = function(abbr, d) {
  if (!d) {
    PEO.els.detailCol.innerHTML = `<div class="panel detail-empty"><div>No records for ${PEO.esc(abbr)} this cycle.</div></div>`;
    return;
  }
  const { fullName, adds, terms } = d;
  const pending  = adds.length + terms.length;
  const addAlert = PEO.getTemplateAlert(fullName, "ADD");
  const termAlert = PEO.getTemplateAlert(fullName, "TERM");
  const anyAlert  = addAlert || termAlert;
  let html = "";

  // Alerta de template
  if (anyAlert) {
    const al = addAlert || termAlert;
    const changes = [
      ...(al.added_fields   || []).map(f => `+ ${f}`),
      ...(al.removed_fields || []).map(f => `- ${f}`),
      ...(al.not_in_pdf     || []).map(f => `⚠ ${f}`),
    ];
    html += `<div class="alert-card">
      <div class="alert-card-title">Template changed — verify before generating</div>
      ${changes.slice(0, 6).map(c => `<div class="alert-change">${PEO.esc(c)}</div>`).join("")}
      ${changes.length > 6 ? `<div class="alert-change">…+${changes.length - 6} more</div>` : ""}
    </div>`;
  }

  // Alerta de deadline
  if (d.hasOverdue) {
    html += `<div class="alert-card">
      <div class="alert-card-title">⚠ Overdue — immediate action required</div>
      <div class="alert-change">One or more records has passed the ${PEO.state.defaults.reportingDeadlineDays}-day deadline.</div>
    </div>`;
  } else if (d.hasUrgent) {
    html += `<div class="alert-card" style="background:var(--term-bg);border-color:var(--term-bd)">
      <div class="alert-card-title" style="color:var(--term)">⏰ Deadline approaching — ${d.minDaysLeft} day(s) remaining</div>
    </div>`;
  }

  // Badges de resumen
  const badges = [
    adds.length  > 0 ? `<span class="badge badge-add">${adds.length} Add${adds.length > 1 ? "s" : ""}</span>`   : "",
    terms.length > 0 ? `<span class="badge badge-term">${terms.length} Term${terms.length > 1 ? "s" : ""}</span>` : "",
    pending === 0    ? `<span class="badge badge-done">All generated</span>` : "",
    anyAlert         ? `<span class="badge badge-alert">Template alert</span>` : `<span class="badge badge-done">Template OK</span>`,
    d.hasOverdue     ? `<span class="badge badge-alert">Overdue</span>` : d.hasUrgent ? `<span class="badge badge-term">Urgent</span>` : "",
  ].filter(Boolean).join("");

  html += `<div class="panel">
    <div class="state-card-name">${PEO.esc(fullName)}</div>
    <div class="state-card-sub">Template: plantilla_${PEO.esc(abbr)}_*.pdf · Deadline: ${PEO.state.defaults.reportingDeadlineDays}d</div>
    <div class="badges">${badges}</div>
    <div style="margin-top:12px">
      <div class="breakdown-row"><span class="breakdown-label">Pending adds</span><span class="breakdown-value add">${adds.length}</span></div>
      <div class="breakdown-row"><span class="breakdown-label">Pending terms</span><span class="breakdown-value term">${terms.length}</span></div>
      <div class="breakdown-row"><span class="breakdown-label">Already generated</span><span class="breakdown-value">${d.addsDone + d.termsDone}</span></div>
      <div class="breakdown-row"><span class="breakdown-label">Tightest deadline</span><span class="breakdown-value">${d.minDaysLeft === null ? "—" : d.minDaysLeft < 0 ? `<span class="text-alert">${Math.abs(d.minDaysLeft)}d overdue</span>` : `${d.minDaysLeft}d remaining`
      }</span></div>
    </div>
  </div>`;

  // Records with per-row deadline badge
    for (const [proc, rows, cls] of [["ADD", adds, "add"], ["TERM", terms, "term"]]) {
      if (!rows.length) continue;
      html += `<div class="panel"><div class="panel-title">${proc} records (${rows.length})</div><div class="record-list">
      ${rows.slice(0, 10).map(r => {
        const cv = PEO.esc(String(PEO.getRowValue(r, "# Case")).trim());
        const cl = PEO.esc(String(PEO.getRowValue(r, "1. Employer") || "").trim());
        return `<div class="record-item"><span class="record-case">${cv}</span><span class="record-client">${cl}</span>${PEO.deadlineBadge(PEO.daysUntilDeadline(r))}<span class="badge badge-${cls}">${proc}</span></div>`;
      }).join("")}
      ${rows.length > 10 ? `<div style="font-size:11px;color:var(--c-muted);padding-top:4px">…and ${rows.length - 10} more</div>` : ""}
    </div></div>`;
    }

    // Actions
    if (pending > 0) {
      html += `<div class="panel action-group">
      ${adds.length > 0 ? `
        <button class="action-btn primary" onclick="window._peo.generateState('${PEO.esc(abbr)}','ADD')">
          ↗ Generate ${adds.length} ADD PDF${adds.length > 1 ? "s" : ""}
        </button>
        <button class="action-btn" onclick="window._peo.previewState('${PEO.esc(abbr)}','ADD')" style="font-size:11px">
          Preview ADD forms first
        </button>`: ""}
      ${terms.length > 0 ? `
        <button class="action-btn primary" onclick="window._peo.generateState('${PEO.esc(abbr)}','TERM')">
          ↗ Generate ${terms.length} TERM PDF${terms.length > 1 ? "s" : ""}
        </button>
        <button class="action-btn" onclick="window._peo.previewState('${PEO.esc(abbr)}','TERM')" style="font-size:11px">
          Preview TERM forms first
        </button>`: ""}
      <div style="border-top:1px solid var(--border);margin-top:4px;padding-top:8px;display:flex;gap:6px">
        ${adds.length > 0 ? `<button class="action-btn" onclick="window._peo.validateTemplate('${PEO.esc(abbr)}','ADD')" style="flex:1;font-size:10px;text-align:center">Validate ADD template</button>` : ""}
        ${terms.length > 0 ? `<button class="action-btn" onclick="window._peo.validateTemplate('${PEO.esc(abbr)}','TERM')" style="flex:1;font-size:10px;text-align:center">Validate TERM template</button>` : ""}
      </div>
    </div>`;
    }
    html += `<div id="validationBox" class="hidden"></div>`;
    PEO.els.detailCol.innerHTML = html;

};
