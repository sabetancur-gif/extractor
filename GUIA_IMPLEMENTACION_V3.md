# PEO License Manager — Guía de Implementación v3.0
## Paso a Paso Completo · Senior Engineering Guide

---

> **Versión base analizada:** v2.4  
> **Objetivo:** v3.0 con arquitectura JSON-first, roles granulares, panel de control, recomendaciones inteligentes y reportes mejorados  
> **Filosofía:** Nunca romper lo funcional. Cada mejora es aditiva o reemplaza explícitamente. Todo el código nuevo debe ser comentado y coherente con el estilo existente.

---

## ÍNDICE

1. [VISIÓN GENERAL DE LA ARQUITECTURA v3.0](#1-visión-general)
2. [PASO 1 — Nueva estructura de archivos](#paso-1)
3. [PASO 2 — Migración JSON: states_structures.json y JSONs por estado](#paso-2)
4. [PASO 3 — config.js — Roles y categorías de usuario](#paso-3)
5. [PASO 4 — state.js — Estado global extendido](#paso-4)
6. [PASO 5 — workbook.js — Carga JSON-first con fallback Excel](#paso-5)
7. [PASO 6 — map.js — JSON-first + sección de recomendaciones](#paso-6)
8. [PASO 7 — report.js — Informes mejorados con lógica de roles](#paso-7)
9. [PASO 8 — workbook.js (salida) — CSV adicional + más campos](#paso-8)
10. [PASO 9 — index.html — Botón panel, botón header, modal histórico por rol](#paso-9)
11. [PASO 10 — app.js — Lógica de roles al cargar + botones panel](#paso-10)
12. [PASO 11 — panel.html — Panel de control de registros](#paso-11)
13. [PASO 12 — temperatura.json — Datos de dificultad](#paso-12)
14. [PASO 13 — CSS — Estilos del panel y recomendaciones](#paso-13)
15. [PASO 14 — Orden de scripts en index.html](#paso-14)
16. [CHECKLIST FINAL](#checklist-final)

---

## 1. VISIÓN GENERAL

### Arquitectura v3.0 (flujo de datos)

```
Carpeta del proyecto/
├── data/
│   ├── registros.xlsm          ← FALLBACK (sigue existiendo)
│   ├── states_structures.json  ← NUEVO: estructura de campos por estado/proceso
│   ├── Oregon_ADD.json         ← NUEVO: registros de casos (uno por estado/proceso)
│   ├── Oregon_TERM.json
│   ├── Maryland_ADD.json
│   └── ...
├── temperatura.json            ← NUEVO: dificultad por estado/proceso
├── defaults.json               ← Sin cambios
├── assets/
│   ├── css/
│   │   ├── base.css            ← Sin cambios
│   │   ├── layout.css          ← Sin cambios
│   │   └── components.css      ← EDITAR: agregar estilos panel/recomendaciones
│   └── js/
│       ├── config.js           ← EDITAR: agregar roles, categorías
│       ├── state.js            ← EDITAR: extender estado global
│       ├── workbook.js         ← EDITAR: carga JSON-first + CSV output
│       ├── map.js              ← EDITAR: JSON-first buildStateMap + recomendaciones
│       ├── report.js           ← EDITAR: informes por rol
│       ├── app.js              ← EDITAR: lógica roles al cargar + botones panel
│       ├── json-manager.js     ← NUEVO: CRUD de JSONs por estado/proceso
│       └── recommendations.js  ← NUEVO: motor de recomendaciones
├── index.html                  ← EDITAR: botón panel en header + detailCol
└── panel.html                  ← NUEVO: panel de control independiente
```

### Resumen de cambios por archivo

| Archivo | Acción | Razón |
|---|---|---|
| `config.js` | EDITAR | Agregar categorías de usuario (Creator/Leader/Compliance) |
| `state.js` | EDITAR | Agregar campos para JSON-source, rol activo |
| `workbook.js` | EDITAR | Carga JSON-first con fallback Excel; CSV en salida |
| `map.js` | EDITAR | buildStateMap desde JSON; recomendaciones debajo del mapa |
| `report.js` | EDITAR | Informes diferenciados por rol; paleta mejorada |
| `app.js` | EDITAR | Roles en peo-folder-loaded; botones panel |
| `index.html` | EDITAR | Botón panel header, botón Panel_XX en detailCol |
| `components.css` | EDITAR | Estilos panel + recomendaciones |
| `json-manager.js` | CREAR | Leer/escribir/validar JSONs por estado/proceso |
| `recommendations.js` | CREAR | Motor de recomendaciones basado en temperatura.json |
| `panel.html` | CREAR | Página independiente del panel de control |
| `states_structures.json` | CREAR | Estructura de campos (migrar desde Fields_Templates) |
| `temperatura.json` | CREAR | Dificultad por estado/proceso |
| `{Estado}_{Proceso}.json` | CREAR | Un archivo por combinación de estado/proceso |

---

## PASO 1 — Nueva estructura de archivos

### 1.1 Crear `data/states_structures.json`

Este archivo se construye migrando la hoja `Fields_Templates` del Excel. La estructura es:

```json
{
  "Oregon": {
    "ADD": {
      "nombre_campo_pdf": {
        "field_pdf": "nombre_campo_pdf",
        "required": true,
        "placeholder": "Enter employer name"
      },
      "effective_date": {
        "field_pdf": "effective_date",
        "required": true,
        "placeholder": "MM/DD/YYYY"
      },
      "notes": {
        "field_pdf": "notes",
        "required": false,
        "placeholder": "Optional notes"
      }
    },
    "TERM": {
      "termination_date": {
        "field_pdf": "termination_date",
        "required": true,
        "placeholder": "MM/DD/YYYY"
      }
    }
  },
  "Maryland": {
    "ADD": { ... },
    "TERM": { ... }
  }
}
```

**Regla de migración desde Excel:**
- Cada fila de `Fields_Templates` donde `Estado = Oregon` y `Proceso = ADD` genera una entrada.
- `field_pdf` → clave del diccionario AND valor de `"field_pdf"`.
- `required`: si `header_excel` es igual a `"No completar"` → `false`, cualquier otro valor → `true`.
- `placeholder` → valor directo de la columna `Placeholder`.

**Script de migración (ejecutar una sola vez en `extraccion.html` o en Python):**

Abrir `extraccion.html` del proyecto (ya existe) y ejecutar este snippet en la consola del navegador después de cargar el workbook:

```javascript
// Pegar esto en la consola de extraccion.html con el workbook cargado
function migrateToStatesStructures(workbook) {
  const ws = workbook.Sheets["Fields_Templates"];
  const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });
  const result = {};

  for (const row of rows) {
    const estado   = String(row["Estado"]       || "").trim();
    const proceso  = String(row["Proceso"]      || "").trim().toUpperCase();
    const fieldPdf = String(row["field_pdf"]    || "").trim();
    const header   = String(row["header_excel"] || "").trim();
    const ph       = String(row["Placeholder"]  || "").trim();

    if (!estado || !proceso || !fieldPdf) continue;
    if (!result[estado]) result[estado] = {};
    if (!result[estado][proceso]) result[estado][proceso] = {};

    result[estado][proceso][fieldPdf] = {
      field_pdf:   fieldPdf,
      required:    header.toLowerCase() !== "no completar",
      placeholder: ph || `Enter ${fieldPdf.replace(/_/g, " ")}`,
    };
  }
  return result;
}
// Uso: console.log(JSON.stringify(migrateToStatesStructures(WORKBOOK_CARGADO), null, 2))
// Copiar output y guardar como data/states_structures.json
```

---

### 1.2 Crear `{Estado}_{Proceso}.json` por cada combinación

**Formato del archivo (ej: `data/Oregon_ADD.json`):**

```json
{
  "_meta": {
    "state": "Oregon",
    "process": "ADD",
    "version": "3.0",
    "last_updated": "2026-05-01"
  },
  "records": [
    {
      "# Case": "PEO-001-2026",
      "Creado": "",
      "1. Employer": "Acme Corp",
      "effective_date": "04/15/2026",
      "employee_name": "John Doe",
      "ssn": "***-**-1234"
    },
    {
      "# Case": "PEO-002-2026",
      "Creado": "SI",
      "1. Employer": "Beta LLC",
      "effective_date": "04/20/2026",
      "employee_name": "Jane Smith",
      "ssn": "***-**-5678"
    }
  ]
}
```

**Script de migración desde la hoja Data del Excel (ejecutar en consola de extraccion.html):**

```javascript
function migrateDataToJsonFiles(workbook) {
  const ws   = workbook.Sheets["Data"];
  const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });
  const byKey = {};

  for (const row of rows) {
    const estado  = String(row["Estado"]  || "").trim();
    const proceso = String(row["Proceso"] || "").trim().toUpperCase();
    if (!estado || !["ADD","TERM"].includes(proceso)) continue;
    const key = `${estado}_${proceso}`;
    if (!byKey[key]) byKey[key] = { state: estado, process: proceso, records: [] };
    byKey[key].records.push({ ...row });
  }

  const results = {};
  for (const [key, val] of Object.entries(byKey)) {
    results[key] = {
      _meta: {
        state:        val.state,
        process:      val.process,
        version:      "3.0",
        last_updated: new Date().toISOString().slice(0, 10),
      },
      records: val.records,
    };
  }
  return results;
  // Para cada clave en results, descargar como {clave}.json en la carpeta data/
}
```

---

### 1.3 Crear `temperatura.json`

Crear en la raíz del proyecto (junto a `index.html`):

```json
{
  "Oregon_ADD": {
    "valor_dificultad_proceso": 72,
    "valor_dificultad_formulario": 65
  },
  "Oregon_TERM": {
    "valor_dificultad_proceso": 58,
    "valor_dificultad_formulario": 50
  },
  "Maryland_ADD": {
    "valor_dificultad_proceso": 80,
    "valor_dificultad_formulario": 75
  },
  "Maryland_TERM": {
    "valor_dificultad_proceso": 68,
    "valor_dificultad_formulario": 60
  },
  "Arkansas_ADD": {
    "valor_dificultad_proceso": 45,
    "valor_dificultad_formulario": 40
  },
  "Arkansas_TERM": {
    "valor_dificultad_proceso": 38,
    "valor_dificultad_formulario": 35
  },
  "Florida_ADD": {
    "valor_dificultad_proceso": 55,
    "valor_dificultad_formulario": 50
  },
  "Hawaii_ADD": {
    "valor_dificultad_proceso": 70,
    "valor_dificultad_formulario": 65
  },
  "Hawaii_TERM": {
    "valor_dificultad_proceso": 62,
    "valor_dificultad_formulario": 58
  },
  "Idaho_ADD": {
    "valor_dificultad_proceso": 48,
    "valor_dificultad_formulario": 42
  },
  "Idaho_TERM": {
    "valor_dificultad_proceso": 40,
    "valor_dificultad_formulario": 35
  },
  "Kansas_ADD": {
    "valor_dificultad_proceso": 50,
    "valor_dificultad_formulario": 45
  },
  "Massachusetts_ADD": {
    "valor_dificultad_proceso": 85,
    "valor_dificultad_formulario": 80
  },
  "Massachusetts_TERM": {
    "valor_dificultad_proceso": 75,
    "valor_dificultad_formulario": 70
  },
  "Nebraska_ADD": {
    "valor_dificultad_proceso": 52,
    "valor_dificultad_formulario": 48
  },
  "Nebraska_TERM": {
    "valor_dificultad_proceso": 45,
    "valor_dificultad_formulario": 40
  },
  "New Jersey_ADD": {
    "valor_dificultad_proceso": 78,
    "valor_dificultad_formulario": 72
  },
  "New Jersey_TERM": {
    "valor_dificultad_proceso": 70,
    "valor_dificultad_formulario": 65
  },
  "New York_ADD": {
    "valor_dificultad_proceso": 88,
    "valor_dificultad_formulario": 85
  },
  "New York_TERM": {
    "valor_dificultad_proceso": 82,
    "valor_dificultad_formulario": 78
  },
  "South Carolina_ADD": {
    "valor_dificultad_proceso": 55,
    "valor_dificultad_formulario": 50
  },
  "South Carolina_TERM": {
    "valor_dificultad_proceso": 48,
    "valor_dificultad_formulario": 42
  },
  "Utah_ADD": {
    "valor_dificultad_proceso": 60,
    "valor_dificultad_formulario": 55
  },
  "Utah_TERM": {
    "valor_dificultad_proceso": 52,
    "valor_dificultad_formulario": 48
  },
  "Wisconsin_TERM": {
    "valor_dificultad_proceso": 44,
    "valor_dificultad_formulario": 38
  },
  "Connecticut_TERM": {
    "valor_dificultad_proceso": 66,
    "valor_dificultad_formulario": 60
  }
}
```

---

## PASO 2 — Crear `assets/js/json-manager.js` (NUEVO)

Crear el archivo `/assets/js/json-manager.js` con el siguiente contenido completo:

```javascript
/* global PEO */
/* json-manager.js — Lectura, escritura y gestión de JSONs por estado/proceso — v3.0 */
"use strict";

// ── Estado de carga de JSONs ───────────────────────────────────────────────
PEO.jsonData = {
  statesStructures: null,   // contenido de states_structures.json
  records: {},              // { "Oregon_ADD": { _meta, records: [] }, ... }
  temperatura: null,        // contenido de temperatura.json
};

// ── Carga de states_structures.json ───────────────────────────────────────
PEO.loadStatesStructures = async function() {
  const f = PEO.findFile("states_structures.json");
  if (!f) {
    PEO.notify("states_structures.json not found — JSON mode unavailable.", "info");
    return false;
  }
  try {
    PEO.jsonData.statesStructures = JSON.parse(await f.text());
    return true;
  } catch(e) {
    PEO.notify("Error parsing states_structures.json: " + e.message, "err");
    return false;
  }
};

// ── Carga de temperatura.json ──────────────────────────────────────────────
PEO.loadTemperatura = async function() {
  const f = PEO.findFile("temperatura.json");
  if (!f) { PEO.jsonData.temperatura = {}; return; }
  try {
    PEO.jsonData.temperatura = JSON.parse(await f.text());
  } catch(e) {
    PEO.jsonData.temperatura = {};
    PEO.notify("Error parsing temperatura.json: " + e.message, "err");
  }
};

// ── Carga de todos los JSONs de estado/proceso encontrados ─────────────────
PEO.loadAllStateJsons = async function() {
  PEO.jsonData.records = {};
  // Buscar archivos que matcheen el patrón {Estado}_{Proceso}.json
  const pattern = /^(.+)_(ADD|TERM)\.json$/i;
  for (const [key, file] of PEO.state.files) {
    const fname = file.name;
    const match = fname.match(pattern);
    if (!match) continue;
    try {
      const content = JSON.parse(await file.text());
      const jsonKey = `${match[1]}_${match[2].toUpperCase()}`;
      PEO.jsonData.records[jsonKey] = content;
    } catch(e) {
      PEO.notify(`Error parsing ${fname}: ${e.message}`, "err");
    }
  }
};

// ── Obtener registros para un estado/proceso desde JSON ───────────────────
PEO.getJsonRecords = function(stateName, proceso) {
  const key = `${stateName}_${proceso.toUpperCase()}`;
  return PEO.jsonData.records[key]?.records || null;
};

// ── Guardar cambios en un JSON de estado/proceso (vía descarga) ───────────
PEO.saveStateJson = function(stateName, proceso, records) {
  const key     = `${stateName}_${proceso.toUpperCase()}`;
  const existing = PEO.jsonData.records[key];
  const updated  = {
    _meta: {
      ...(existing?._meta || {}),
      state:        stateName,
      process:      proceso.toUpperCase(),
      version:      "3.0",
      last_updated: new Date().toISOString().slice(0, 10),
    },
    records,
  };
  PEO.jsonData.records[key] = updated;

  // Trigger descarga del archivo actualizado
  const blob  = new Blob([JSON.stringify(updated, null, 2)], { type: "application/json" });
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement("a");
  a.href      = url;
  a.download  = `${stateName}_${proceso.toUpperCase()}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  PEO.notify(`Saved: ${a.download}`, "ok");
};

// ── Marcar un registro como "Creado: SI" en JSON ──────────────────────────
PEO.setJsonRecordCreado = function(stateName, proceso, caseNum, value = "SI") {
  const key     = `${stateName}_${proceso.toUpperCase()}`;
  const jsonObj = PEO.jsonData.records[key];
  if (!jsonObj) return;
  const rec = jsonObj.records.find(r => String(r["# Case"]).trim() === String(caseNum).trim());
  if (rec) rec["Creado"] = value;
};

// ── Construir stateMap desde JSONs (JSON-first) ────────────────────────────
// Retorna el mismo formato que buildStateMap desde Excel para compatibilidad total
PEO.buildStateMapFromJson = function() {
  if (!PEO.jsonData.records || !Object.keys(PEO.jsonData.records).length) return null;
  const map = {};
  for (const [key, jsonObj] of Object.entries(PEO.jsonData.records)) {
    if (!jsonObj?.records) continue;
    const meta    = jsonObj._meta || {};
    const stateName = meta.state;
    const proceso   = (meta.process || "").toUpperCase();
    if (!stateName || !["ADD","TERM"].includes(proceso)) continue;
    const abbr = PEO.nameToAbbr(stateName);
    if (!abbr) continue;

    if (!map[abbr]) map[abbr] = {
      fullName: stateName, adds: [], terms: [],
      addsDone: 0, termsDone: 0,
      minDaysLeft: null, hasOverdue: false, hasUrgent: false,
      source: "json",
    };

    for (const row of jsonObj.records) {
      const created = PEO.isCreated(row["Creado"]);
      const days    = PEO.daysUntilDeadline(row);
      if (proceso === "ADD") {
        if (!created) { map[abbr].adds.push(row); _trackDeadlineJson(map[abbr], days); }
        else map[abbr].addsDone++;
      } else {
        if (!created) { map[abbr].terms.push(row); _trackDeadlineJson(map[abbr], days); }
        else map[abbr].termsDone++;
      }
    }
  }
  return Object.keys(map).length ? map : null;
};

function _trackDeadlineJson(e, days) {
  if (days === null) return;
  if (e.minDaysLeft === null || days < e.minDaysLeft) e.minDaysLeft = days;
  if (days < 0)  e.hasOverdue = true;
  if (days <= 7) e.hasUrgent  = true;
}

// ── Obtener la estructura de campos requeridos para estado/proceso ─────────
PEO.getRequiredFields = function(stateName, proceso) {
  const ss = PEO.jsonData.statesStructures;
  if (!ss || !ss[stateName] || !ss[stateName][proceso]) return [];
  return Object.values(ss[stateName][proceso])
    .filter(f => f.required)
    .map(f => ({ field_pdf: f.field_pdf, placeholder: f.placeholder }));
};

// ── Obtener dificultad de temperatura.json para un estado/proceso ──────────
PEO.getTemperatura = function(stateName, proceso) {
  const key = `${stateName}_${proceso}`;
  return PEO.jsonData.temperatura?.[key] || { valor_dificultad_proceso: 50, valor_dificultad_formulario: 50 };
};
```

---

## PASO 3 — Editar `assets/js/config.js`

### Bloque a AGREGAR al final de `config.js` (después de `PEO.LEADER_OPERATORS`):

```javascript
// ──── Categorías de usuario (v3.0) ────────────────────────────────────────
// Creator: Santiago Betancur — acceso total
// Leader:  Carlos Peralta, Yoryam Sanchez — dashboard completo, sin crear formularios
// Compliance: todos los demás — solo sus métricas, sin fecha histórico manual

PEO.USER_ROLES = {
  "Santiago Betancur": "creator",
  "Carlos Peralta":    "leader",
  "Yoryam Sanchez":    "leader",
  "Mateo Bedoya":      "compliance",
  "Isabella Cano":     "compliance",
  "Paulina Montes":    "compliance",
};

// Determinar rol de un usuario
PEO.getUserRole = function(username) {
  return PEO.USER_ROLES[username] || "compliance";
};

// Helpers de rol
PEO.isCreator    = u => PEO.getUserRole(u) === "creator";
PEO.isLeader     = u => ["creator","leader"].includes(PEO.getUserRole(u));
PEO.isCompliance = u => PEO.getUserRole(u) === "compliance";

// Rango automático para histórico Compliance (últimos 4 meses)
PEO.getComplianceHistoricoCutoff = function() {
  const d = new Date();
  d.setMonth(d.getMonth() - 4);
  return d.toISOString().slice(0, 10); // "YYYY-MM-DD"
};
```

---

## PASO 4 — Editar `assets/js/state.js`

### 4.1 Agregar campos al objeto `PEO.state`

Localizar el bloque:
```javascript
PEO.state = {
  files:           new Map(),
  ...
  _kpiQueue: [],
};
```

**Reemplazar** `_kpiQueue: [],` con:
```javascript
  _kpiQueue: [],
  jsonMode:        false,    // true = datos vienen de JSON; false = fallback Excel
  userRole:        "compliance", // rol del usuario activo: creator|leader|compliance
  statesStructures: null,    // referencia a PEO.jsonData.statesStructures
};
```

### 4.2 Agregar a `PEO.els` los nuevos elementos del DOM

Localizar el cierre de `PEO.els = {`:

Agregar al final de `PEO.els` (antes del cierre `};`):
```javascript
  get btnOpenPanel()   { return PEO.$("btnOpenPanel"); },
  get recommendSection(){ return PEO.$("recommendSection"); },
```

---

## PASO 5 — Editar `assets/js/workbook.js`

### 5.1 Reemplazar la función `PEO.loadFolder`

Localizar el bloque completo:
```javascript
PEO.loadFolder = async function(files) {
  PEO.state.files.clear();
  ...
  PEO.els.folderStatus.textContent = `${files.length} files · ${PEO.state.session.username}`;
};
```

**Reemplazar con:**

```javascript
// ── Carga de carpeta — JSON-first con fallback Excel ───────────────────────
PEO.loadFolder = async function(files) {
  PEO.state.files.clear();
  PEO.state.workbookFile  = null;
  PEO.state.currentRows   = [];
  PEO.state.selectedState = null;
  PEO.state.jsonMode      = false;
  if (PEO.state.preview.liveUrl) URL.revokeObjectURL(PEO.state.preview.liveUrl);

  for (const f of files) {
    PEO.state.files.set(PEO.fileKey(f), f);
    if (/registros\.(xlsm|xlsx)$/i.test(f.name)) PEO.state.workbookFile = f;
    if (/historico_informe\.xlsx$/i.test(f.name)) PEO.state.historicoFile = f;
  }

  const loadErr = PEO.$(\"loadError\");
  if (loadErr) { loadErr.style.color = \"var(--add)\"; loadErr.style.display = \"block\"; loadErr.textContent = \"Loading JSON data…\"; }
  await new Promise(r => setTimeout(r, 30));

  // ── Determinar rol del usuario activo ─────────────────────────────────
  const username = PEO.state.selectedUser || \"\";
  PEO.state.userRole = PEO.getUserRole(username);

  // ── INTENTO JSON-FIRST ─────────────────────────────────────────────────
  const ssOk = await PEO.loadStatesStructures();
  if (ssOk) {
    await PEO.loadAllStateJsons();
    const jsonMap = PEO.buildStateMapFromJson();
    if (jsonMap && Object.keys(jsonMap).length > 0) {
      PEO.state.jsonMode = true;
      PEO.notify(\"JSON mode active — loaded \" + Object.keys(PEO.jsonData.records).length + \" state/process file(s).\", \"ok\");
    }
  }

  // ── FALLBACK EXCEL (si JSON-first no produjo datos) ────────────────────
  if (!PEO.state.jsonMode) {
    if (!PEO.state.workbookFile) {
      throw new Error(\"registros.xlsm not found and no valid JSON data loaded.\");
    }
    if (loadErr) loadErr.textContent = \"Reading workbook (fallback)…\";
    await new Promise(r => setTimeout(r, 20));
    PEO.state.workbook = XLSX.read(await PEO.state.workbookFile.arrayBuffer(), { type: \"array\" });
    PEO.state.currentRows = PEO.readDataRows();
    PEO.notify(\"Excel fallback mode — states_structures.json not found or empty.\", \"info\");
  }

  // ── Temperatura siempre se carga ───────────────────────────────────────
  await PEO.loadTemperatura();

  if (loadErr) loadErr.textContent = \"Loading session…\";
  await PEO.loadSession();

  if (PEO.state.selectedUser) {
    PEO.state.session.username = PEO.state.selectedUser;
    if (PEO.els.sessionUser) PEO.els.sessionUser.textContent = PEO.state.selectedUser;
  }
  await PEO.loadValidationReport();
  await PEO.loadDefaults();

  // ── Modal histórico: solo si es Leader o Creator ───────────────────────
  if (PEO.state.historicoFile) {
    if (PEO.isCompliance(username)) {
      // Compliance: fecha automática = últimos 4 meses, sin modal
      PEO.state.historicoCutoffDate = PEO.getComplianceHistoricoCutoff();
      PEO.notify(\"Historic period: last 4 months (auto)\", \"info\");
    } else {
      // Leader / Creator: mostrar modal para confirmar fecha
      if (loadErr) loadErr.textContent = \"Historic file found…\";
      PEO.state.historicoCutoffDate = await PEO.showHistoricoCutoffModal(
        PEO.state.historicoFile.name
      );
    }
  }

  if (loadErr) loadErr.style.display = \"none\";

  // ── Construir mapa y renderizar ────────────────────────────────────────
  const sm = PEO.state.jsonMode
    ? PEO.buildStateMapFromJson()
    : PEO.buildStateMap(PEO.state.currentRows);

  PEO.updateKPIBar(sm);
  PEO.buildTileMap(sm);
  PEO.renderDetailEmpty();

  // ── Renderizar sección de recomendaciones ──────────────────────────────
  if (typeof PEO.renderRecommendations === \"function\") {
    PEO.renderRecommendations(sm);
  }

  PEO.els.loadScreen.classList.add(\"hidden\");
  PEO.els.appBody.classList.remove(\"hidden\");
  PEO.notify(`Folder loaded — ${files.length} file(s).`, \"ok\");
  document.dispatchEvent(new CustomEvent(\"peo-folder-loaded\"));
  PEO.els.folderStatus.textContent = `${files.length} files · ${PEO.state.session.username}`;
};
```

### 5.2 Reemplazar `PEO.refreshAll` para ser JSON-aware

Localizar:
```javascript
PEO.refreshAll = function() {
  PEO.state.currentRows = PEO.readDataRows();
  const sm = PEO.buildStateMap(PEO.state.currentRows);
  ...
};
```

**Reemplazar con:**

```javascript
// ── Refresh completo de KPI + mapa + detalle (JSON-aware) ─────────────────
PEO.refreshAll = function() {
  // JSON-first o fallback Excel
  let sm;
  if (PEO.state.jsonMode) {
    sm = PEO.buildStateMapFromJson();
  } else {
    PEO.state.currentRows = PEO.readDataRows();
    sm = PEO.buildStateMap(PEO.state.currentRows);
  }
  PEO.updateKPIBar(sm);
  PEO.buildTileMap(sm);
  // Actualizar recomendaciones
  if (typeof PEO.renderRecommendations === "function") {
    PEO.renderRecommendations(sm);
  }
  if (PEO.state.selectedState && sm[PEO.state.selectedState]) {
    PEO.renderDetail(PEO.state.selectedState, sm[PEO.state.selectedState]);
    document.querySelectorAll(".state-tile").forEach(el => {
      if (el.dataset.abbr === PEO.state.selectedState) el.classList.add("sel");
    });
  } else {
    PEO.renderDetailEmpty();
  }
};
```

---

## PASO 6 — Editar `assets/js/generate.js`

### 6.1 En `PEO.doGenerate` — después de `PEO.setRowValue(row, "Creado", "SI")`

Localizar en ambas ramas (outputDirHandle y ZIP):
```javascript
PEO.setRowValue(row, "Creado", "SI");
```

**Después de cada una agregar:**
```javascript
// En modo JSON, también marcar en el JSON en memoria
if (PEO.state.jsonMode) {
  PEO.setJsonRecordCreado(stateName, proceso, cv, "SI");
}
```

Esto asegura que al hacer refreshAll, el JSON refleje el estado correcto.

---

## PASO 7 — Crear `assets/js/recommendations.js` (NUEVO)

Crear `/assets/js/recommendations.js`:

```javascript
/* global PEO */
/* recommendations.js — Motor de recomendaciones basado en temperatura.json — v3.0 */
"use strict";

// ── Renderizar sección de recomendaciones debajo del mapa ──────────────────
PEO.renderRecommendations = function(stateMap) {
  const container = PEO.$("recommendSection");
  if (!container) return;

  const temp  = PEO.jsonData.temperatura || {};
  const items = [];

  // Construir lista de oportunidades: estado+proceso con formularios pendientes
  for (const [abbr, data] of Object.entries(stateMap || {})) {
    const stateName = data.fullName;
    if (data.adds.length > 0) {
      const key  = `${stateName}_ADD`;
      const t    = temp[key] || { valor_dificultad_proceso: 50, valor_dificultad_formulario: 50 };
      const score = _computeScore(data.adds.length, t, data.hasOverdue, data.hasUrgent);
      items.push({ abbr, stateName, proceso: "ADD", pending: data.adds.length, t, score,
                   overdue: data.hasOverdue, urgent: data.hasUrgent });
    }
    if (data.terms.length > 0) {
      const key  = `${stateName}_TERM`;
      const t    = temp[key] || { valor_dificultad_proceso: 50, valor_dificultad_formulario: 50 };
      const score = _computeScore(data.terms.length, t, data.hasOverdue, data.hasUrgent);
      items.push({ abbr, stateName, proceso: "TERM", pending: data.terms.length, t, score,
                   overdue: data.hasOverdue, urgent: data.hasUrgent });
    }
  }

  if (!items.length) {
    container.innerHTML = "";
    container.style.display = "none";
    return;
  }

  // Ordenar: mayor score primero (más urgente/difícil primero)
  items.sort((a, b) => b.score - a.score);
  container.style.display = "block";
  container.innerHTML = _buildRecommendHTML(items);
};

// ── Calcular score de prioridad ────────────────────────────────────────────
// Fórmula: (dificultad_proceso * 0.4 + dificultad_formulario * 0.3 + pending*2) * urgencyFactor
function _computeScore(pending, t, overdue, urgent) {
  const base    = (t.valor_dificultad_proceso * 0.4) + (t.valor_dificultad_formulario * 0.3) + (pending * 2);
  const urgency = overdue ? 2.0 : urgent ? 1.5 : 1.0;
  return Math.round(base * urgency);
}

// ── Construir HTML de recomendaciones ─────────────────────────────────────
function _buildRecommendHTML(items) {
  const top = items.slice(0, 6); // máximo 6 recomendaciones

  const cards = top.map((item, idx) => {
    const rank   = idx + 1;
    const dProc  = item.t.valor_dificultad_proceso;
    const dForm  = item.t.valor_dificultad_formulario;
    const difAvg = Math.round((dProc + dForm) / 2);
    const color  = difAvg >= 75 ? "var(--alert)" : difAvg >= 55 ? "var(--term)" : "var(--done)";
    const label  = difAvg >= 75 ? "High" : difAvg >= 55 ? "Medium" : "Low";
    const urgTag = item.overdue
      ? `<span class="rec-tag rec-overdue">⚠ Overdue</span>`
      : item.urgent ? `<span class="rec-tag rec-urgent">⏰ Urgent</span>` : "";
    const procColor = item.proceso === "ADD" ? "var(--add)" : "var(--term)";

    return `
      <div class="rec-card" title="Score: ${item.score}">
        <div class="rec-rank">${rank}</div>
        <div class="rec-body">
          <div class="rec-header">
            <span class="rec-state">${PEO.esc(item.stateName)}</span>
            <span class="rec-proc" style="color:${procColor}">${item.proceso}</span>
            ${urgTag}
          </div>
          <div class="rec-meta">
            <span class="rec-pending">${item.pending} form${item.pending>1?"s":""} pending</span>
            <span class="rec-dif" style="color:${color}">Difficulty: ${label} (${difAvg})</span>
          </div>
          <div class="rec-bars">
            <div class="rec-bar-wrap">
              <span class="rec-bar-label">Process</span>
              <div class="rec-bar-track">
                <div class="rec-bar-fill" style="width:${dProc}%;background:${color}"></div>
              </div>
              <span class="rec-bar-val">${dProc}</span>
            </div>
            <div class="rec-bar-wrap">
              <span class="rec-bar-label">Forms</span>
              <div class="rec-bar-track">
                <div class="rec-bar-fill" style="width:${dForm}%;background:${color}"></div>
              </div>
              <span class="rec-bar-val">${dForm}</span>
            </div>
          </div>
        </div>
      </div>`;
  }).join("");

  return `
    <div class="rec-section">
      <div class="rec-title">
        <span class="rec-title-icon">🧭</span>
        <div>
          <div class="rec-title-main">Recommended Workflow</div>
          <div class="rec-title-sub">Sorted by priority: complexity + urgency + volume — tackle these first</div>
        </div>
      </div>
      <div class="rec-grid">${cards}</div>
      ${items.length > 6 ? `<div class="rec-more">+${items.length-6} more pending combinations</div>` : ""}
    </div>`;
}
```

---

## PASO 8 — Editar `assets/js/report.js`

### 8.1 Reemplazar `PEO.generateAllReports` (SECTION 11)

Localizar el bloque completo `PEO.generateAllReports = async function()...`

**Reemplazar con:**

```javascript
// ═══════════════════════════════════════════════════════════════════════════
//  SECTION 11 — Main Coordinator (v3.0 — role-aware)
// ═══════════════════════════════════════════════════════════════════════════

PEO.generateAllReports = async function() {
  const generated = PEO.state._kpiQueue.filter(e => e.action === "GENERATE");
  const username  = PEO.state.selectedUser || PEO.state.session.username || "";
  const role      = PEO.getUserRole(username);

  if (!generated.length) {
    PEO.notify("No forms generated this session — nothing to report.", "info");
    return;
  }

  PEO.notify("Generating session reports…", "info");
  const stats    = PEO.buildSessionStats();
  const histRows = await _readHistoricoRows(PEO.state.historicoCutoffDate);

  // ── Compliance: solo su propio dashboard, sin info de otros ───────────
  if (role === "compliance") {
    const sessionFileName = PEO.buildSessionExcel(stats);
    await new Promise(r => setTimeout(r, 300));
    // Solo reporte individual — filtrado, sin datos de equipo
    PEO.generateComplianceDashboard(stats, histRows.filter(h =>
      String(h["Operator"] || h.operador || "").trim().toLowerCase() ===
      username.trim().toLowerCase()
    ));
    await PEO.buildHistorico(stats, sessionFileName);
    return;
  }

  // ── Leader / Creator: flujo completo ──────────────────────────────────
  const sessionFileName = PEO.buildSessionExcel(stats);
  await new Promise(r => setTimeout(r, 300));
  PEO.generatePdfReport(stats, histRows);
  await PEO.buildHistorico(stats, sessionFileName);
};

// ── Reporte de líder bajo selección de operador ────────────────────────────
PEO.generateLeaderReport = async function(targetOperator) {
  const histRows = await _readHistoricoRows(PEO.state.historicoCutoffDate);
  if (!histRows.length) {
    PEO.notify("No historic data available for leader report.", "info");
    return;
  }
  // Si se pasa un operador específico, filtrar su reporte individual
  if (targetOperator) {
    const filtered = histRows.filter(h =>
      String(h["Operator"] || h.operador || "").trim().toLowerCase() ===
      targetOperator.trim().toLowerCase()
    );
    const mockStats = _buildStatsFromHistoric(filtered, targetOperator);
    PEO.generatePdfReport(mockStats, filtered);
    return;
  }
  // Sin operador: reporte de líder con todo el equipo
  _generateFullLeaderReport(histRows);
};

// ── Helper: construir stats mockup desde datos históricos de un operador ──
function _buildStatsFromHistoric(rows, operator) {
  let totalForms = 0, adds = 0, terms = 0, totalSec = 0;
  const byState = {};
  for (const r of rows) {
    const f  = Number(r["Total Forms"] || r.total_formularios) || 0;
    const a  = Number(r["ADDs"]  || r.adds)  || 0;
    const t  = Number(r["TERMs"] || r.terms) || 0;
    const s  = Number(r["Total Sec"] || r.tiempo_total_seg) || 0;
    totalForms += f; adds += a; terms += t; totalSec += s;
    const det = String(r["State Detail"] || r.detalle_estados || "");
    det.split(" | ").forEach(piece => {
      if (!piece.includes(":")) return;
      const [st, ct] = piece.split(":");
      if (!byState[st.trim()]) byState[st.trim()] = { ADD: 0, TERM: 0, total: 0, totalSec: 0 };
      byState[st.trim()].total += parseInt(ct.trim()) || 0;
    });
  }
  const avgSec = totalForms > 0 ? (totalSec / totalForms).toFixed(1) : "0";
  return {
    operator: operator, date: new Date().toISOString().slice(0, 10),
    datetime: new Date().toISOString().slice(0, 16).replace("T", " "),
    totalForms, byProcess: { ADD: adds, TERM: terms },
    stateCount: Object.keys(byState).length, byState,
    totalSec: totalSec.toFixed(1), avgSec, formsPerHr: "—",
    sessionStart: "", sessionEnd: "",
  };
}
```

### 8.2 Agregar `PEO.generateComplianceDashboard` (NUEVO en report.js)

Agregar al final de `report.js`, antes de la última línea:

```javascript
// ═══════════════════════════════════════════════════════════════════════════
//  SECTION 12 — Compliance Personal Dashboard (v3.0)
//  Solo métricas del operador, sin datos de equipo ni de otros perfiles
// ═══════════════════════════════════════════════════════════════════════════

PEO.generateComplianceDashboard = function(stats, myHistRows) {
  myHistRows = myHistRows || [];
  const C    = RPT_C;

  // Métricas personales históricas
  const myTotalSessions = myHistRows.length;
  const myAllTimeForms  = myHistRows.reduce((s, h) => s + (Number(h["Total Forms"]||h.total_formularios)||0), 0);
  const myBestSession   = myHistRows.reduce((best, h) => {
    const f = Number(h["Total Forms"]||h.total_formularios)||0;
    return f > best ? f : best;
  }, 0);
  const myAvgForms = myTotalSessions > 0 ? (myAllTimeForms / myTotalSessions).toFixed(1) : "0";
  const mySparkForms = myHistRows.slice(-8).map(h => Number(h["Total Forms"]||h.total_formularios)||0);
  const addRatio = stats.totalForms > 0
    ? Math.round(((stats.byProcess.ADD||0) / stats.totalForms) * 100) : 0;

  // Tabla de historial personal (últimas 8 sesiones)
  const histRows8 = myHistRows.slice(-8).map((h, i) => {
    const f   = Number(h["Total Forms"]||h.total_formularios)||0;
    const sec = Number(h["Total Sec"]||h.tiempo_total_seg)||0;
    const fph = f > 0 && sec > 0 ? (f/(sec/3600)).toFixed(1) : "—";
    return `<tr class="${i%2?"even":""}">
      <td class="td-l">${PEO.esc(String(h["Date"]||h.fecha_realizacion||"").slice(0,16))}</td>
      <td class="td-c fw7">${f}</td>
      <td class="td-c"><span class="ba">${h["ADDs"]||h.adds||0}</span></td>
      <td class="td-c"><span class="bt">${h["TERMs"]||h.terms||0}</span></td>
      <td class="td-c">${h["States"]||h.estados||0}</td>
      <td class="td-c mu">${sec > 0 ? (sec/f).toFixed(1)+"s" : "—"}</td>
      <td class="td-c" style="color:${C.blue700};font-weight:700">${fph !== "—" ? fph+"/hr" : "—"}</td>
    </tr>`;
  }).join("");

  const html = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <title>My Dashboard · ${PEO.esc(stats.operator)} · ${stats.date}</title>
    <style>${_reportCSS(false)}
      .dash-hero{background:linear-gradient(135deg,${C.blue900},${C.blue800});color:#E2E8F0;
        padding:28px 36px;border-radius:0 0 18px 18px;margin-bottom:24px;}
      .dash-hero-name{font-size:26px;font-weight:900;letter-spacing:-.5px}
      .dash-hero-sub{font-size:13px;opacity:.75;margin-top:4px}
      .progress-ring{display:flex;align-items:center;gap:28px;padding:14px 22px;
        background:${C.blue50};border-radius:10px;margin:12px 0;}
      .prog-label{font-size:11px;color:${C.gray500};font-weight:700;text-transform:uppercase;letter-spacing:.06em}
      .prog-val{font-size:28px;font-weight:900;color:${C.blue700};line-height:1}
      .prog-sub{font-size:11px;color:${C.gray500};margin-top:2px}
    </style></head><body>
    <div class="pbar"><span>⚖ PEO License Manager &nbsp;·&nbsp; My Dashboard &nbsp;·&nbsp; ${PEO.esc(stats.operator)}</span>
    <button onclick="window.print()">⬇ Save as PDF</button></div>
    <div class="dash-hero">
      <div class="dash-hero-name">${PEO.esc(stats.operator)}</div>
      <div class="dash-hero-sub">Personal Performance Dashboard · ${stats.datetime}</div>
    </div>
    <div style="margin:0 28px">
    <!-- KPIs esta sesión -->
    <div class="block">
      <div class="block-header bh1"><span class="block-num">01</span>
        <span class="block-title">This Session</span>
        <span class="block-sub">${stats.datetime}</span></div>
      <div class="kpi-strip">
        <div class="kc"><div class="kv">${stats.totalForms}</div><div class="kl">Forms Generated</div></div>
        <div class="kc"><div class="kv blue">${stats.byProcess.ADD||0}</div><div class="kl">ADD Forms</div></div>
        <div class="kc"><div class="kv red">${stats.byProcess.TERM||0}</div><div class="kl">TERM Forms</div></div>
        <div class="kc"><div class="kv">${stats.stateCount}</div><div class="kl">States</div></div>
        <div class="kc"><div class="kv">${stats.avgSec}s</div><div class="kl">Avg / Form</div></div>
        <div class="kc"><div class="kv">${stats.formsPerHr}</div><div class="kl">Forms / hr</div></div>
      </div>
      <div style="padding:0 22px 14px">
        <div class="progress-ring">
          <div>${_svgDonut(stats.byProcess.ADD||0, stats.byProcess.TERM||0)}</div>
          <div>
            <div class="prog-label">ADD Ratio</div>
            <div class="prog-val">${addRatio}%</div>
            <div class="prog-sub">of ${stats.totalForms} total forms</div>
          </div>
          <div style="margin-left:auto">
            <div class="prog-label">Forms Distribution by State</div>
            ${_svgBarChart(stats.byState)}
          </div>
        </div>
      </div>
    </div>
    <!-- Mi historial -->
    <div class="block">
      <div class="block-header bh2"><span class="block-num">02</span>
        <span class="block-title">My Personal History</span>
        <span class="block-sub">${myTotalSessions} recorded sessions</span></div>
      <div style="padding:12px 22px;display:flex;gap:16px;flex-wrap:wrap;align-items:center">
        <div class="sc"><div class="sc-l">All-Time Forms</div><div class="sc-v">${myAllTimeForms}</div></div>
        <div class="sc"><div class="sc-l">Best Session</div><div class="sc-v">${myBestSession}</div></div>
        <div class="sc"><div class="sc-l">Avg per Session</div><div class="sc-v">${myAvgForms}</div></div>
        <div class="sc"><div class="sc-l">Total Sessions</div><div class="sc-v">${myTotalSessions}</div></div>
        ${mySparkForms.length >= 2 ? `<div><div class="chart-title" style="font-size:10px;margin-bottom:4px">My Trend (last ${mySparkForms.length})</div>
          ${_svgSparkline(mySparkForms, C.blue600)}</div>` : ""}
      </div>
      ${histRows8 ? `<table class="dt"><thead><tr>
        <th>Date</th><th>Forms</th><th>ADD</th><th>TERM</th><th>States</th><th>Avg Sec</th><th>Forms/hr</th>
        </tr></thead><tbody>${histRows8}</tbody></table>` :
        `<p class="no-data">Load historico_informe.xlsx to see your history.</p>`}
    </div>
    </div>
    <div class="ftr">
      <span>PEO License Manager · Personal Dashboard · Auto-generated · ${stats.datetime}</span>
      <span>Operator: ${PEO.esc(stats.operator)} · ${stats.totalForms} form(s)</span>
    </div>
    </body></html>`;

  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const win  = window.open(url, "_blank");
  if (!win) PEO.notify("Enable pop-ups to view the Dashboard.", "err");
  setTimeout(() => URL.revokeObjectURL(url), 15000);
};
```

---

## PASO 9 — Editar `assets/js/workbook.js` (salida CSV)

### 9.1 Agregar generación de CSV en `PEO.buildSessionExcel`

Localizar al final de `PEO.buildSessionExcel`, justo antes de `return fname;` (o antes del último bloque que hace el download):

Después de la línea `a.click();` del xlsx, **agregar:**

```javascript
  // ── CSV adicional de la misma sesión ────────────────────────────────────
  {
    const csvRows = rows.length ? rows : [{ "State":"—","Process":"—","# Case":"—",
      "PDF File Created":"—","Download Path":"—","Date Completed":"—","Operator":"—",
      "Duration (sec)":"—","State Full Name":"—","Week Number":"—","Month":"—" }];
    const headers = Object.keys(csvRows[0]);
    const csvLines = [
      headers.join(","),
      ...csvRows.map(r => headers.map(h => `"${String(r[h]??"")}"`).join(","))
    ];
    const csvBlob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8" });
    const csvUrl  = URL.createObjectURL(csvBlob);
    const csvA    = document.createElement("a");
    csvA.href     = csvUrl;
    csvA.download = fname.replace(".xlsx", ".csv");
    csvA.click();
    setTimeout(() => URL.revokeObjectURL(csvUrl), 2000);
    PEO.notify("CSV also exported: " + csvA.download, "ok");
  }
```

### 9.2 Agregar más campos en `PEO.buildSessionExcel`

Localizar en `buildSessionExcel` donde se construye el array `rows`:
```javascript
const rows = events.map(e => ({
  "State":            e.state     || "—",
  ...
}));
```

**Reemplazar** con:
```javascript
  const weekNum = (dt) => {
    const d  = new Date(dt);
    const s  = new Date(d.getFullYear(), 0, 1);
    return Math.ceil(((d - s) / 86400000 + s.getDay() + 1) / 7);
  };

  const rows = events.map(e => ({
    "State":              e.state      || "—",
    "State Full Name":    PEO.ABBR_TO_NAME?.[e.state] || e.state || "—",
    "Process":            e.process    || "—",
    "# Case":             e.case       || "—",
    "PDF File Created":   e.file       || "—",
    "Download Path":      outputLabel,
    "Date Completed":     String(e.timestamp || stats.datetime).slice(0, 16).replace("T", " "),
    "Operator":           e.username   || stats.operator,
    "Duration (sec)":     parseFloat(e.duration_sec || 0).toFixed(1),
    "Week Number":        weekNum(e.timestamp || stats.datetime),
    "Month":              new Date(e.timestamp || stats.datetime).toLocaleString("en-US", { month: "long" }),
    "Session Total Forms": stats.totalForms,
    "Session ADDs":        stats.byProcess.ADD  || 0,
    "Session TERMs":       stats.byProcess.TERM || 0,
    "JSON Mode":           PEO.state.jsonMode ? "Yes" : "No (Excel fallback)",
  }));
```

### 9.3 Agregar CSV al histórico en `PEO.buildHistorico`

Localizar en `PEO.buildHistorico` justo después del bloque que hace click en el enlace `.xlsx`:
```javascript
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  PEO.notify("Historic updated: ...
```

**Antes** de ese notify, agregar:
```javascript
  // ── CSV del histórico ─────────────────────────────────────────────────
  {
    const csvHeaders = Object.keys(allRows[0] || {});
    const csvLines   = [
      csvHeaders.join(","),
      ...allRows.map(r => csvHeaders.map(h => `"${String(r[h]??"")}"`).join(","))
    ];
    const csvBlob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8" });
    const csvUrl  = URL.createObjectURL(csvBlob);
    const csvA    = document.createElement("a");
    csvA.href     = csvUrl;
    csvA.download = fname.replace(".xlsx", ".csv");
    csvA.click();
    setTimeout(() => URL.revokeObjectURL(csvUrl), 2000);
  }
```

---

## PASO 10 — Editar `assets/js/app.js`

### 10.1 Reemplazar el listener `peo-folder-loaded` (Leader Report button)

Localizar el bloque:
```javascript
document.addEventListener("peo-folder-loaded", () => {
  const user = PEO.state.session.username || PEO.state.selectedUser || "";
  const btn  = PEO.$("btnLeaderReport");
  if (btn && PEO.LEADER_OPERATORS && PEO.LEADER_OPERATORS.includes(user)) {
    btn.style.display = "";
    ...
  }
});
```

**Reemplazar con:**
```javascript
// ── Configurar UI según rol del usuario ─────────────────────────────────────
document.addEventListener("peo-folder-loaded", () => {
  const user = PEO.state.selectedUser || PEO.state.session.username || "";
  const role = PEO.getUserRole(user);

  // ── Botón Leader Report: visible para leader y creator ────────────────
  const btnLR = PEO.$("btnLeaderReport");
  if (btnLR) {
    if (PEO.isLeader(user)) {
      btnLR.style.display    = "";
      btnLR.style.background = "linear-gradient(135deg,#1D4ED8,#0C1F4A)";
      btnLR.style.color      = "#fff";
      btnLR.style.fontWeight = "700";
    } else {
      btnLR.style.display = "none";
    }
  }

  // ── Botón "Save workbook" oculto para Compliance (no necesita crear formularios externamente) ─
  // Los compliance SÍ generan PDFs — el botón Save sigue visible para todos

  // ── Indicador de modo JSON en folderStatus ─────────────────────────────
  const modeTag = PEO.state.jsonMode ? " · JSON" : " · Excel";
  const sb = PEO.$("folderStatus");
  if (sb) sb.textContent = sb.textContent + modeTag;

  // ── Botón de panel en header siempre visible ───────────────────────────
  const btnPanel = PEO.$("btnOpenPanel");
  if (btnPanel) btnPanel.style.display = "";
});
```

### 10.2 Agregar evento para el botón panel en header

En `attachEvents()`, después de la línea:
```javascript
on("btnLeaderReport",  "click", () => PEO.generateLeaderReport());
```

**Agregar:**
```javascript
// ── Abrir panel de control (sin estado preseleccionado) ────────────────────
on("btnOpenPanel", "click", () => {
  const url = "panel.html";
  window.open(url, "_blank");
});
```

### 10.3 Agregar función `openPanelForState` al objeto `window._peo`

Localizar:
```javascript
window._peo = {
  previewState:     PEO.previewState,
  generateState:    PEO.generateState,
  validateTemplate: PEO.validateTemplate,
};
```

**Reemplazar con:**
```javascript
window._peo = {
  previewState:     PEO.previewState,
  generateState:    PEO.generateState,
  validateTemplate: PEO.validateTemplate,
  // Abrir panel con estado preseleccionado
  openPanelForState: function(abbr) {
    const stateName = PEO.ABBR_TO_NAME[abbr] || abbr;
    const url = `panel.html?state=${encodeURIComponent(stateName)}`;
    window.open(url, "_blank");
  },
  // Generar reporte individual para un operador (líder)
  generateIndividualReport: function(operatorName) {
    PEO.generateLeaderReport(operatorName);
  },
};
```

---

## PASO 11 — Editar `assets/js/map.js`

### 11.1 En `PEO.renderDetail` — agregar botón Panel_XX

Localizar dentro de `PEO.renderDetail`, donde se construye la variable `html` inicial:
```javascript
let html = "";

// Alerta de template
if (anyAlert) {
```

**Reemplazar** `let html = "";` con:

```javascript
  const abbr3 = abbr; // usar variable local para closures
  // Botón Panel_XX al inicio del panel de detalle (disponible para todos los roles)
  let html = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <button class="main-btn panel-state-btn"
        onclick="window._peo.openPanelForState('${PEO.esc(abbr3)}')"
        title="Open records panel for ${PEO.esc(fullName)}">
        <span style="font-size:14px">📋</span> Panel_${PEO.esc(abbr3)}
      </button>
    </div>`;
```

---

## PASO 12 — Editar `index.html`

### 12.1 Agregar botón panel en el header

Localizar el bloque del header:
```html
<button class="theme-toggle" id="btnTheme" title="Toggle light / dark mode">🌙</button>
```

**Antes** de ese botón, agregar:
```html
<button class="main-btn" id="btnOpenPanel" title="Open Records Control Panel" style="display:none">
  <span style="font-size:14px">🗂</span>
</button>
```

### 12.2 Agregar contenedor de recomendaciones en el app body

Localizar dentro de `<div class="app-body hidden" id="appBody">`, después del cierre del tile-grid y antes de `<div class="detail-col" id="detailCol">`:

Primero identificar la estructura del layout. Buscar:
```html
</div><!-- fin stateGrid o mapSection -->
```

Agregar después del mapa (en el contenedor principal, debajo del grid de estados):
```html
<!-- ── Sección de recomendaciones (debajo del mapa) ──────────── -->
<div id="recommendSection" style="display:none"></div>
```

Si el layout tiene un contenedor principal tipo:
```html
<div class="main-layout">
  <div class="map-col">
    <div class="state-grid" id="stateGrid"></div>
  </div>
  <div class="detail-col" id="detailCol"></div>
</div>
```

Agregar `<div id="recommendSection">` **fuera** del `main-layout`, inmediatamente después.

### 12.3 Agregar `<script>` tags para los nuevos archivos

Localizar el bloque de scripts al final de `index.html`. El orden es crítico. Ver Paso 14.

---

## PASO 13 — Crear `panel.html` (NUEVO)

Crear el archivo `panel.html` en la raíz del proyecto. Este es un HTML independiente que carga los mismos CSS y una versión simplificada de la lógica.

```html
<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Records Control Panel — PEO License Manager</title>
  <link rel="stylesheet" href="./assets/css/base.css" />
  <link rel="stylesheet" href="./assets/css/layout.css" />
  <link rel="stylesheet" href="./assets/css/components.css" />
  <style>
    /* ── Estilos específicos del panel ──────────────────────────── */
    body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; }

    .panel-header {
      background: var(--header-bg);
      backdrop-filter: var(--header-blur);
      border-bottom: 1px solid var(--border);
      padding: 14px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .panel-header-brand {
      font-size: 15px;
      font-weight: 800;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .panel-header-actions { margin-left: auto; display: flex; gap: 8px; align-items: center; }

    .panel-body { padding: 24px; max-width: 1100px; margin: 0 auto; }

    .panel-selectors {
      display: flex;
      gap: 12px;
      align-items: flex-end;
      flex-wrap: wrap;
      margin-bottom: 24px;
    }
    .panel-selector-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .panel-selector-group label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--muted);
    }
    .panel-select {
      padding: 9px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface2);
      color: var(--text);
      font-size: 13px;
      font-family: inherit;
      min-width: 160px;
      cursor: pointer;
    }

    /* Tabla de registros */
    .records-table-wrap { overflow-x: auto; margin-top: 16px; }
    .records-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    .records-table th {
      background: var(--surface2);
      color: var(--muted);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .06em;
      padding: 8px 10px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }
    .records-table td {
      padding: 8px 10px;
      border-bottom: 1px solid var(--border);
      color: var(--text);
      vertical-align: middle;
    }
    .records-table tr:hover td { background: var(--surface2); }
    .records-table .td-case { font-weight: 700; color: var(--add); font-family: monospace; }
    .records-table .td-creado-si { color: var(--done); font-weight: 700; }
    .records-table .td-creado-no { color: var(--muted); }

    /* Formulario de edición inline */
    .field-input {
      width: 100%;
      padding: 5px 8px;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: var(--surface);
      color: var(--text);
      font-size: 12px;
      font-family: inherit;
    }
    .field-input:focus { border-color: var(--add); outline: none; }

    /* Badges */
    .badge-si  { background: var(--done-bg);  color: var(--done);  border: 1px solid var(--done-bd);  padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
    .badge-no  { background: var(--surface2); color: var(--muted); border: 1px solid var(--border);   padding: 2px 7px; border-radius: 4px; font-size: 10px; }

    /* Action row */
    .panel-actions-row {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: center;
    }

    .panel-empty {
      text-align: center;
      padding: 48px;
      color: var(--muted);
      font-size: 14px;
    }
    .panel-empty-icon { font-size: 40px; margin-bottom: 12px; }

    /* Modal nuevo registro */
    .new-rec-form { display: flex; flex-direction: column; gap: 12px; }
    .new-rec-form .field-group { display: flex; flex-direction: column; gap: 4px; }
    .new-rec-form label { font-size: 11px; font-weight: 700; text-transform: uppercase;
      letter-spacing: .06em; color: var(--muted); }
    .required-star { color: var(--alert); }

    .no-data-banner {
      background: var(--alert-bg);
      border: 1px solid var(--alert-bd);
      border-radius: var(--radius);
      padding: 12px 16px;
      font-size: 12px;
      color: var(--alert);
      margin-bottom: 16px;
    }
    .info-banner {
      background: var(--add-bg);
      border: 1px solid var(--add-bd);
      border-radius: var(--radius);
      padding: 12px 16px;
      font-size: 12px;
      color: var(--add);
      margin-bottom: 16px;
    }
  </style>
</head>
<body>

<!-- Header del panel -->
<header class="panel-header">
  <div class="panel-header-brand">
    <span style="font-size:20px">🗂</span>
    Records Control Panel
    <span style="font-size:11px;font-weight:400;color:var(--muted);margin-left:4px">PEO License Manager v3.0</span>
  </div>
  <div class="panel-header-actions">
    <span id="panelModeTag" style="font-size:11px;color:var(--muted)">Standalone mode</span>
    <button class="theme-toggle" id="panelBtnTheme" title="Toggle theme">🌙</button>
    <button class="main-btn" onclick="window.close()">✕ Close</button>
  </div>
</header>

<!-- Body del panel -->
<div class="panel-body">

  <!-- Instrucciones de carga -->
  <div id="panelLoadSection">
    <div class="info-banner">
      📂 To manage records, first load the project folder. This panel reads and saves
      <strong>{State}_{Process}.json</strong> files from your project directory.
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px">
      <div>
        <input type="file" id="panelFolderInput" webkitdirectory multiple hidden />
        <button class="main-btn cta" onclick="document.getElementById('panelFolderInput').click()">
          📁 Load Project Folder
        </button>
      </div>
    </div>
  </div>

  <!-- Selectores de estado y proceso -->
  <div class="panel-selectors">
    <div class="panel-selector-group">
      <label>State</label>
      <select id="panelStateSelect" class="panel-select">
        <option value="">— Select State —</option>
      </select>
    </div>
    <div class="panel-selector-group">
      <label>Process</label>
      <select id="panelProcessSelect" class="panel-select">
        <option value="">— Select Process —</option>
        <option value="ADD">ADD</option>
        <option value="TERM">TERM</option>
      </select>
    </div>
    <button class="main-btn cta" id="panelLoadBtn" onclick="panelLoadRecords()">
      Load Records
    </button>
    <button class="main-btn" id="panelNewBtn" onclick="panelShowNewModal()" style="display:none">
      ＋ New Record
    </button>
    <button class="main-btn" id="panelSaveBtn" onclick="panelSaveRecords()" style="display:none;background:var(--done);color:#fff">
      ✓ Save Changes
    </button>
  </div>

  <!-- Tabla de registros -->
  <div id="panelTableSection">
    <div class="panel-empty">
      <div class="panel-empty-icon">📋</div>
      <div>Select a state and process, then click <strong>Load Records</strong>.</div>
    </div>
  </div>

</div>

<!-- Modal nuevo registro -->
<div id="panelNewModal" class="modal-overlay" style="display:none">
  <div style="background:var(--surface);border-radius:14px;padding:28px 32px;
              max-width:560px;width:90vw;max-height:85vh;overflow-y:auto;
              border:1px solid var(--border);box-shadow:var(--shadow-lg)">
    <div style="font-size:15px;font-weight:800;margin-bottom:16px">New Record</div>
    <div id="newRecFormBody" class="new-rec-form"></div>
    <div style="display:flex;gap:8px;margin-top:20px">
      <button class="main-btn cta" id="panelNewSaveBtn" onclick="panelSaveNewRecord()">Save Record</button>
      <button class="main-btn" onclick="panelCloseNewModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Scripts: reutilizamos config.js para ABBR_TO_NAME, NAME_TO_ABBR, etc. -->
<script src="./assets/vendor/xlsx.full.min.js"></script>
<script>window.PEO = window.PEO || {};</script>
<script src="./assets/js/config.js"></script>
<script src="./assets/js/theme.js"></script>

<script>
/* Panel Controller — inline script para el panel independiente */
"use strict";

// ── Estado del panel ─────────────────────────────────────────────────────
const PANEL = {
  files:            new Map(),
  statesStructures: null,
  records:          {},      // { "Oregon_ADD": { _meta, records } }
  currentState:     null,
  currentProcess:   null,
  currentRecords:   [],
  dirtyRows:        new Set(), // índices de filas modificadas
};

// ── Inicialización del tema ───────────────────────────────────────────────
document.getElementById("panelBtnTheme").addEventListener("click", () => {
  const html  = document.documentElement;
  const theme = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", theme);
  document.getElementById("panelBtnTheme").textContent = theme === "dark" ? "🌙" : "☀️";
});

// ── Leer parámetro de URL para preseleccionar estado ─────────────────────
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const stParam = params.get("state");
  if (stParam) {
    document.getElementById("panelStateSelect").value = stParam;
  }
});

// ── Carga de archivos del proyecto ───────────────────────────────────────
document.getElementById("panelFolderInput").addEventListener("change", async function() {
  const files = [...this.files];
  if (!files.length) return;
  PANEL.files.clear();
  PANEL.statesStructures = null;
  PANEL.records = {};

  for (const f of files) {
    const key = f.name.toLowerCase().replace(/\\/g, "/");
    PANEL.files.set(key, f);
  }

  // Cargar states_structures.json
  for (const [key, f] of PANEL.files) {
    if (key.endsWith("states_structures.json")) {
      try { PANEL.statesStructures = JSON.parse(await f.text()); } catch {}
      break;
    }
  }

  // Cargar todos los {Estado}_{Proceso}.json
  const pattern = /^(.+)_(add|term)\.json$/i;
  for (const [key, f] of PANEL.files) {
    const fname = f.name;
    const match = fname.match(pattern);
    if (!match) continue;
    try {
      const content = JSON.parse(await f.text());
      const jsonKey = `${match[1]}_${match[2].toUpperCase()}`;
      PANEL.records[jsonKey] = content;
    } catch {}
  }

  // Poblar el selector de estados con los disponibles
  const stateNames = new Set();
  for (const key of Object.keys(PANEL.records)) {
    const [stateName] = key.split("_ADD").concat(key.split("_TERM"));
    // extraer nombre antes del último _ADD o _TERM
    const parts = key.split("_");
    parts.pop(); // quitar ADD o TERM
    stateNames.add(parts.join("_"));
  }

  const sel = document.getElementById("panelStateSelect");
  sel.innerHTML = '<option value="">— Select State —</option>';
  const sorted = [...stateNames].sort();
  for (const sn of sorted) {
    const opt = document.createElement("option");
    opt.value = sn; opt.textContent = sn;
    sel.appendChild(opt);
  }

  // Leer parámetro de URL para autoseleccionar
  const params = new URLSearchParams(window.location.search);
  const stParam = params.get("state");
  if (stParam) sel.value = stParam;

  document.getElementById("panelModeTag").textContent =
    PANEL.statesStructures ? "JSON mode ✓" : "JSON mode (no structure file)";
  document.getElementById("panelLoadSection").style.display = "none";
  alert(`Loaded ${Object.keys(PANEL.records).length} state/process file(s).`);
});

// ── Cargar registros en la tabla ─────────────────────────────────────────
function panelLoadRecords() {
  const state   = document.getElementById("panelStateSelect").value;
  const process = document.getElementById("panelProcessSelect").value;
  if (!state || !process) { alert("Please select both State and Process."); return; }

  const key = `${state}_${process}`;
  const json = PANEL.records[key];

  PANEL.currentState   = state;
  PANEL.currentProcess = process;
  PANEL.dirtyRows      = new Set();

  if (!json || !json.records) {
    PANEL.currentRecords = [];
    document.getElementById("panelTableSection").innerHTML =
      `<div class="no-data-banner">No records found for <strong>${state} ${process}</strong>.
       Create the first record with the button below.</div>`;
    document.getElementById("panelNewBtn").style.display  = "";
    document.getElementById("panelSaveBtn").style.display = "";
    return;
  }

  PANEL.currentRecords = JSON.parse(JSON.stringify(json.records)); // deep copy
  renderPanelTable();
  document.getElementById("panelNewBtn").style.display  = "";
  document.getElementById("panelSaveBtn").style.display = "";
}

// ── Renderizar tabla de registros ─────────────────────────────────────────
function renderPanelTable() {
  const records = PANEL.currentRecords;
  if (!records.length) {
    document.getElementById("panelTableSection").innerHTML =
      `<div class="panel-empty"><div class="panel-empty-icon">📋</div>
       <div>No records yet. Click <strong>+ New Record</strong> to add one.</div></div>`;
    return;
  }

  // Obtener campos requeridos para esta combinación
  const reqFields = _getPanelRequiredFields();

  // Columnas: # Case, Creado, + campos requeridos, + actions
  const cols = ["# Case", "Creado", ...reqFields.map(f => f.field_pdf)];

  let thead = `<tr>
    ${cols.map(c => `<th>${_escHtml(c.replace(/_/g," "))}</th>`).join("")}
    <th style="width:100px">Actions</th>
  </tr>`;

  let tbody = records.map((rec, idx) => {
    const isCreado = ["si","sí","yes","true","1"].includes(String(rec["Creado"]||"").toLowerCase());
    const cells = cols.map(col => {
      if (col === "Creado") {
        return `<td><span class="${isCreado ? "badge-si" : "badge-no"}">${isCreado ? "SI" : "—"}</span></td>`;
      }
      if (col === "# Case") {
        return `<td class="td-case">${_escHtml(String(rec[col]||""))}</td>`;
      }
      const val = rec[col] || "";
      return `<td><input class="field-input" data-row="${idx}" data-col="${_escHtml(col)}"
        value="${_escHtml(val)}" oninput="panelFieldChanged(this)" /></td>`;
    });
    return `<tr id="panel-row-${idx}" class="${PANEL.dirtyRows.has(idx) ? "row-dirty" : ""}">
      ${cells.join("")}
      <td style="white-space:nowrap">
        <button class="main-btn" style="font-size:10px;padding:3px 8px"
          onclick="panelToggleCreado(${idx})">${isCreado ? "Undo" : "✓ Done"}</button>
        <button class="main-btn" style="font-size:10px;padding:3px 8px;color:var(--alert);margin-top:4px"
          onclick="panelDeleteRecord(${idx})">✕</button>
      </td>
    </tr>`;
  }).join("");

  document.getElementById("panelTableSection").innerHTML = `
    <div class="panel-actions-row">
      <span style="font-size:12px;color:var(--muted)">${records.length} record(s) ·
        ${records.filter(r => ["si","sí","yes"].includes(String(r["Creado"]||"").toLowerCase())).length} completed</span>
    </div>
    <div class="records-table-wrap">
      <table class="records-table">
        <thead>${thead}</thead>
        <tbody id="panelTableBody">${tbody}</tbody>
      </table>
    </div>`;
}

// ── Obtener campos requeridos del structure JSON ──────────────────────────
function _getPanelRequiredFields() {
  const ss = PANEL.statesStructures;
  if (!ss || !ss[PANEL.currentState] || !ss[PANEL.currentState][PANEL.currentProcess]) return [];
  return Object.values(ss[PANEL.currentState][PANEL.currentProcess])
    .filter(f => f.required)
    .map(f => ({ field_pdf: f.field_pdf, placeholder: f.placeholder || "" }));
}

// ── Handler: campo editado en tabla ──────────────────────────────────────
function panelFieldChanged(input) {
  const idx = parseInt(input.dataset.row);
  const col = input.dataset.col;
  PANEL.currentRecords[idx][col] = input.value;
  PANEL.dirtyRows.add(idx);
  const row = document.getElementById(`panel-row-${idx}`);
  if (row) row.style.background = "var(--add-bg)";
}

// ── Toggle Creado ─────────────────────────────────────────────────────────
function panelToggleCreado(idx) {
  const rec = PANEL.currentRecords[idx];
  const curr = String(rec["Creado"] || "").toLowerCase();
  rec["Creado"] = ["si","sí","yes"].includes(curr) ? "" : "SI";
  PANEL.dirtyRows.add(idx);
  renderPanelTable();
}

// ── Eliminar registro ─────────────────────────────────────────────────────
function panelDeleteRecord(idx) {
  if (!confirm("Delete this record? This cannot be undone until you Save Changes.")) return;
  PANEL.currentRecords.splice(idx, 1);
  renderPanelTable();
}

// ── Guardar cambios ───────────────────────────────────────────────────────
function panelSaveRecords() {
  if (!PANEL.currentState || !PANEL.currentProcess) { alert("No records loaded."); return; }
  const key      = `${PANEL.currentState}_${PANEL.currentProcess}`;
  const existing = PANEL.records[key] || { _meta: {} };
  const updated  = {
    _meta: {
      ...existing._meta,
      state:        PANEL.currentState,
      process:      PANEL.currentProcess,
      version:      "3.0",
      last_updated: new Date().toISOString().slice(0, 10),
    },
    records: PANEL.currentRecords,
  };
  PANEL.records[key] = updated;

  const blob  = new Blob([JSON.stringify(updated, null, 2)], { type: "application/json" });
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement("a");
  a.href      = url;
  a.download  = `${PANEL.currentState}_${PANEL.currentProcess}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  PANEL.dirtyRows.clear();
  alert(`Saved: ${a.download}\n\nReplace the file in your project folder with this download.`);
  renderPanelTable();
}

// ── Modal nuevo registro ──────────────────────────────────────────────────
function panelShowNewModal() {
  if (!PANEL.currentState || !PANEL.currentProcess) {
    alert("Load a state/process first."); return;
  }
  const reqFields = _getPanelRequiredFields();
  const formBody  = document.getElementById("newRecFormBody");

  let formHtml = `
    <div class="field-group">
      <label># Case <span class="required-star">*</span></label>
      <input class="field-input" id="nrf_case" placeholder="PEO-XXX-2026" />
    </div>`;

  for (const f of reqFields) {
    formHtml += `
      <div class="field-group">
        <label>${_escHtml(f.field_pdf.replace(/_/g," "))} <span class="required-star">*</span></label>
        <input class="field-input" id="nrf_${_escHtml(f.field_pdf)}"
          placeholder="${_escHtml(f.placeholder)}" />
      </div>`;
  }

  formBody.innerHTML = formHtml;
  document.getElementById("panelNewModal").style.display = "flex";
}

function panelCloseNewModal() {
  document.getElementById("panelNewModal").style.display = "none";
}

function panelSaveNewRecord() {
  const caseVal = document.getElementById("nrf_case")?.value.trim();
  if (!caseVal) { alert("# Case is required."); return; }

  const reqFields  = _getPanelRequiredFields();
  const newRec     = { "# Case": caseVal, "Creado": "" };

  for (const f of reqFields) {
    const input = document.getElementById(`nrf_${f.field_pdf}`);
    if (input) newRec[f.field_pdf] = input.value.trim();
  }

  PANEL.currentRecords.push(newRec);
  panelCloseNewModal();
  renderPanelTable();
}

// ── Utility ──────────────────────────────────────────────────────────────
function _escHtml(s) {
  return String(s ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;");
}
</script>
</body>
</html>
```

---

## PASO 14 — Agregar estilos en `assets/css/components.css`

Agregar al final del archivo `components.css`:

```css
/* ═══════════════════════════════════════════════════════════════
   RECOMENDACIONES — v3.0
═══════════════════════════════════════════════════════════════ */

.rec-section {
  margin: 20px 0 24px;
  padding: 0 4px;
}

.rec-title {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}
.rec-title-icon { font-size: 22px; margin-top: 2px; }
.rec-title-main {
  font-size: 14px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -.2px;
}
.rec-title-sub {
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
  line-height: 1.5;
}

.rec-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}

.rec-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  transition: border-color .18s, box-shadow .18s;
}
.rec-card:hover {
  border-color: var(--add);
  box-shadow: var(--shadow-md);
}

.rec-rank {
  font-size: 22px;
  font-weight: 900;
  color: var(--subtle);
  min-width: 28px;
  text-align: center;
  padding-top: 2px;
}

.rec-body { flex: 1; min-width: 0; }

.rec-header {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.rec-state {
  font-size: 13px;
  font-weight: 800;
  color: var(--text);
}
.rec-proc {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  background: var(--surface2);
  border-radius: 4px;
  border: 1px solid var(--border);
}

.rec-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
}
.rec-overdue { background: var(--alert-bg); color: var(--alert); border: 1px solid var(--alert-bd); }
.rec-urgent  { background: var(--term-bg);  color: var(--term);  border: 1px solid var(--term-bd); }

.rec-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.rec-pending { font-size: 11px; color: var(--muted); }
.rec-dif     { font-size: 11px; font-weight: 700; }

.rec-bars { display: flex; flex-direction: column; gap: 4px; }
.rec-bar-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}
.rec-bar-label { font-size: 9px; color: var(--muted); min-width: 38px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
.rec-bar-track {
  flex: 1;
  height: 5px;
  background: var(--surface2);
  border-radius: 3px;
  overflow: hidden;
}
.rec-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width .4s ease;
}
.rec-bar-val { font-size: 9px; color: var(--muted); min-width: 22px; text-align: right; font-weight: 700; }

.rec-more {
  text-align: center;
  font-size: 11px;
  color: var(--muted);
  padding-top: 8px;
}

/* ── Botón Panel_XX en el detail panel ─────────────────────────────────── */
.panel-state-btn {
  background: linear-gradient(135deg, var(--surface2), var(--surface));
  border: 1px solid var(--border2);
  color: var(--text);
  font-size: 11px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: var(--radius);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: border-color .18s, background .18s;
}
.panel-state-btn:hover {
  border-color: var(--add);
  color: var(--add);
  background: var(--add-bg);
}
```

---

## PASO 15 — Actualizar `index.html`: orden de scripts

Localizar el bloque de `<script>` al final de `index.html`. El orden correcto en v3.0 debe ser:

```html
<!-- Vendors -->
<script src="./assets/vendor/pdf-lib.min.js"></script>
<script src="./assets/vendor/xlsx.full.min.js"></script>

<!-- Core namespace -->
<script>window.PEO = window.PEO || {};</script>

<!-- Config (primero: define constantes, roles) -->
<script src="./assets/js/config.js"></script>

<!-- Utilities puras (sin DOM) -->
<script src="./assets/js/utils.js"></script>
<script src="./assets/js/theme.js"></script>

<!-- Estado global y referencias DOM -->
<script src="./assets/js/state.js"></script>

<!-- JSON Manager (NUEVO — antes de workbook) -->
<script src="./assets/js/json-manager.js"></script>

<!-- Módulos funcionales -->
<script src="./assets/js/defaults.js"></script>
<script src="./assets/js/canvas.js"></script>
<script src="./assets/js/pdf.js"></script>
<script src="./assets/js/editor.js"></script>
<script src="./assets/js/preview.js"></script>
<script src="./assets/js/progress.js"></script>
<script src="./assets/js/zip.js"></script>
<script src="./assets/js/generate.js"></script>
<script src="./assets/js/map.js"></script>
<script src="./assets/js/workbook.js"></script>
<script src="./assets/js/state-instructions.js"></script>

<!-- Recomendaciones (NUEVO — después de map y workbook) -->
<script src="./assets/js/recommendations.js"></script>

<!-- Reportes -->
<script src="./assets/js/report.js"></script>

<!-- Punto de entrada: siempre el último -->
<script src="./assets/js/app.js"></script>
```

---

## PASO 16 — Editar `index.html`: ubicación de `recommendSection`

### Encontrar la estructura del layout principal

El app body tiene un layout de dos columnas (mapa izquierda, detalle derecha). Buscar en `index.html`:

```html
<div class="app-body hidden" id="appBody">
  <!-- KPI bar -->
  <div class="kpi-bar">...</div>
  
  <!-- Layout principal -->
  <div class="main-layout">  <!-- o similar -->
    <div class="map-col">
      ...
      <div class="state-grid" id="stateGrid"></div>
    </div>
    <div class="detail-col" id="detailCol"></div>
  </div>
</div>
```

Agregar `<div id="recommendSection">` **después** del cierre de `.map-col` pero **dentro** del bloque de contenido principal, como tercer elemento en el layout. El objetivo es que aparezca debajo del mapa:

```html
<!-- Después del state-grid y antes o después del detail-col, 
     dependiendo del layout actual de columns -->
<div id="recommendSection" style="display:none;grid-column:1/-1;padding:0 8px"></div>
```

Si el layout usa CSS Grid (como es probable dado el diseño), agregar `grid-column: 1 / -1` para que ocupe todo el ancho.

---

## PASO 17 — Ajustes finales en `app.js`: Leader Report con selector de operador

### Reemplazar el handler de `btnLeaderReport`

Localizar:
```javascript
on("btnLeaderReport",  "click", () => PEO.generateLeaderReport());
```

**Reemplazar con:**
```javascript
on("btnLeaderReport", "click", () => {
  const username = PEO.state.selectedUser || PEO.state.session.username || "";
  const role     = PEO.getUserRole(username);

  // Líderes: mostrar selector de operador o reporte completo
  if (PEO.isLeader(username)) {
    _showLeaderReportModal();
  }
});

// Modal de selección para reporte de líder
function _showLeaderReportModal() {
  const complianceUsers = PEO.OPERATORS.filter(op => PEO.getUserRole(op) === "compliance");
  const ov = document.createElement("div");
  ov.className = "modal-overlay open";
  ov.style.zIndex = "600";
  ov.innerHTML = `
    <div style="background:var(--surface);border-radius:14px;padding:28px 32px;
                max-width:420px;width:90vw;border:1px solid var(--border);
                box-shadow:var(--shadow-lg);display:flex;flex-direction:column;gap:14px">
      <div style="font-size:15px;font-weight:800">Generate Report</div>
      <div style="font-size:12px;color:var(--muted)">Select which report to generate:</div>
      <button class="main-btn cta" id="lr-full"
        style="background:linear-gradient(135deg,#1D4ED8,#0C1F4A);color:#fff">
        📊 Full Leader Dashboard (All Team)
      </button>
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                  letter-spacing:.06em;color:var(--muted);margin-top:4px">
        Individual Reports:
      </div>
      ${complianceUsers.map(op =>
        `<button class="main-btn lr-individual" data-op="${PEO.esc(op)}"
          style="text-align:left">
          👤 ${PEO.esc(op)}
        </button>`
      ).join("")}
      <button class="main-btn" id="lr-cancel">Cancel</button>
    </div>`;
  document.body.appendChild(ov);

  ov.querySelector("#lr-full").addEventListener("click", () => {
    ov.remove();
    PEO.generateLeaderReport(); // sin argumento = reporte completo
  });
  ov.querySelectorAll(".lr-individual").forEach(btn => {
    btn.addEventListener("click", () => {
      const op = btn.dataset.op;
      ov.remove();
      PEO.generateLeaderReport(op);
    });
  });
  ov.querySelector("#lr-cancel").addEventListener("click", () => ov.remove());
}
```

---

## CHECKLIST FINAL

Antes de probar, verificar:

### Archivos creados ✓
- [ ] `data/states_structures.json` (migrado desde Fields_Templates)
- [ ] `data/{Estado}_{Proceso}.json` para cada combinación (migrado desde hoja Data)
- [ ] `temperatura.json` en la raíz del proyecto
- [ ] `assets/js/json-manager.js`
- [ ] `assets/js/recommendations.js`
- [ ] `panel.html` en la raíz del proyecto

### Archivos editados ✓
- [ ] `assets/js/config.js` — agregadas categorías y helpers de rol
- [ ] `assets/js/state.js` — extendido `PEO.state` con `jsonMode`, `userRole`; `PEO.els` con nuevos elementos
- [ ] `assets/js/workbook.js` — `loadFolder` JSON-first; `refreshAll` JSON-aware; CSV en exports; más campos en session Excel
- [ ] `assets/js/generate.js` — `setJsonRecordCreado` después de generar PDFs
- [ ] `assets/js/map.js` — botón Panel_XX en `renderDetail`
- [ ] `assets/js/report.js` — `generateAllReports` role-aware; `generateComplianceDashboard` nuevo; `generateLeaderReport` con operador target
- [ ] `assets/js/app.js` — `peo-folder-loaded` por rol; `btnOpenPanel`; `window._peo` extendido; modal Leader Report; `_showLeaderReportModal`
- [ ] `assets/css/components.css` — estilos de recomendaciones y botón panel
- [ ] `index.html` — botón `btnOpenPanel` en header; `<div id="recommendSection">`; orden de scripts correcto

### Pruebas funcionales ✓
1. **Carga JSON-first**: Cargar carpeta con `states_structures.json` y JSONs → modo JSON activo
2. **Fallback Excel**: Cargar carpeta sin JSONs pero con `registros.xlsm` → modo Excel
3. **Compliance**: Login como Mateo/Isabella/Paulina → sin modal histórico, reporte solo personal
4. **Leader**: Login como Carlos/Yoryam → modal histórico visible, botón Leader Report con selector
5. **Creator**: Login como Santiago → todas las funcionalidades
6. **Botón Panel_XX**: Clic en tile del mapa → panel detalle muestra botón → clic abre `panel.html?state=Oregon`
7. **Botón 🗂 en header**: Abre `panel.html` sin preselección
8. **Panel**: Cargar carpeta, seleccionar Oregon + ADD, editar campos, añadir registro, guardar → descarga JSON actualizado
9. **Recomendaciones**: Con `temperatura.json` y datos pendientes → aparecen cards ordenadas por score
10. **CSV**: Al guardar workbook → descarga `.xlsx` y `.csv` de sesión + `.csv` del histórico

---

## NOTAS DE COHERENCIA Y MANTENIMIENTO

### Convenciones de nombre que mantener
- `PEO.` — namespace global, todo va aquí
- `_función` — funciones privadas del módulo (no exportar a `window._peo`)
- `/* comentario */` al inicio de cada función nueva
- Strings de `var(--color)` CSS para todos los colores en código inline

### Fallos comunes a evitar
- **No cambiar el nombre de claves en los JSONs** que ya usa la UI (ej: `"# Case"`, `"Creado"`, `"Estado"`, `"Proceso"`)
- **El panel.html es standalone**: no puede usar `PEO.state.files` del main. Tiene su propio `PANEL` object
- **JSON-first no elimina el Excel**: el xlsx sigue siendo necesario como fallback
- **Compatibilidad de `buildStateMap`**: la versión JSON retorna exactamente el mismo shape `{ abbr: { fullName, adds, terms, addsDone, termsDone, minDaysLeft, hasOverdue, hasUrgent } }` que la versión Excel

### Si se añaden nuevos estados/procesos
1. Agregar a `data/states_structures.json` la nueva clave `NuevoEstado.ADD` con sus campos
2. Crear `data/NuevoEstado_ADD.json` con `_meta` y `records: []`
3. Agregar a `temperatura.json`: `"NuevoEstado_ADD": { "valor_dificultad_proceso": X, "valor_dificultad_formulario": Y }`
4. El panel los detectará automáticamente en la próxima carga de carpeta

### Si se añaden nuevos operadores
1. En `config.js`, agregar a `PEO.OPERATORS`
2. En `PEO.OPERATOR_PASSWORDS`, agregar contraseña
3. En `PEO.USER_ROLES`, asignar categoría: `"compliance"`, `"leader"`, o `"creator"`
4. La lógica de roles se aplica automáticamente

---

*Guía generada por análisis completo del codebase v2.4 — cubre los 8 requerimientos funcionales con acoplamiento modular, coherencia visual y pensamiento de equipo senior.*
