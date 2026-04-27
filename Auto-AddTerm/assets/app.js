/* 
Se declaran como globales las librerías externas usadas en este archivo.
XLSX: para leer/escribir Excel
PDFLib: para manipular PDFs
*/
/* global XLSX, PDFLib */

(() => {
// Se extraen las clases necesarias desde PDFLib
// PDFDocument: para cargar y modificar PDFs
// StandardFonts: para fuentes estándar (usada al actualizar apariencias)
const { PDFDocument, StandardFonts } = PDFLib;

/*
Objeto de estado global de la aplicación.
Guardar TODA la información necesaria durante el ciclo de vida:
- Archivos cargados
- Excel (workbook)
- Filas Actuales
- Estado de la vista previa
- Información de generación de PDFs
*/
const state = {
  files: new Map(),  // Mapa de todos los archivos cargados desde la carpeta
  workbookFile: null, // Archivo Excel original (registros.xlsx) 
  workbook: null,  // Objeto XLSX ya parseado
  currentSheet: "",  // Hoja actual seleccionada (estado_tipo)
  currentRows: [],  // Todas las filas de la hoja activa
  visibleRows: [],  // Filas visibles en la tabla (tras filtros)
  generatedRows: [],
  outputDirLabel: "",
  updatedWorkbookBlob: null, // Blob actualizado del Excel
  preview: {  // Sub-estado exclusivo para la vista previa
    items: [],  // Filas a previsualizar
    index: 0,  // Índice actual
    row: null,  // Fila actual editándose
    templateBytes: null,  // bytes del PDF plantilla
    fieldTypes: new Map(),  //Tipo de campos PDF
    liveUrl: "",  // URL del PDF en vivo
    renderToken: 0  // Token para evitar condiciones de carrera
  }
};

/*
Cache de elementos del DOM.
Se guardan una sola vez para evitar llamadas repetidas a getElementById
*/
const els = {
  alertsArea: document.getElementById("alertsArea"),
  btnCheck: document.getElementById("btnCheck"),
  btnPreview: document.getElementById("btnPreview"),
  btnGenerate: document.getElementById("btnGenerate"),
  btnLoadFolder: document.getElementById("btnLoadFolder"),
  btnSaveWorkbook: document.getElementById("btnSaveWorkbook"),
  btnPickOutput: document.getElementById("btnPickOutput"),
  count: document.getElementById("count"),
  closePreviewModal: document.getElementById("closePreviewModal"),
  estado: document.getElementById("estado"),
  editCurrentPreviewBtn: document.getElementById("editCurrentPreviewBtn"),
  filesList: document.getElementById("filesList"),
  folderInput: document.getElementById("folderInput"),
  folderStatus: document.getElementById("folderStatus"),
  pendingSection: document.getElementById("pendingSection"),
  pendingTable: document.getElementById("pendingTable"),
  previewArea: document.getElementById("previewArea"),
  previewModal: document.getElementById("previewModal"),
  previewModalBody: document.getElementById("previewModalBody"),
  previewSingleFrame: document.getElementById("previewSingleFrame"),
  previewPrevBtn: document.getElementById("previewPrevBtn"),
  previewNextBtn: document.getElementById("previewNextBtn"),
  previewCounter: document.getElementById("previewCounter"),
  previewCaseTitle: document.getElementById("previewCaseTitle"),
  resultArea: document.getElementById("resultArea"),
  status: document.getElementById("status"),
  searchCase: document.getElementById("searchCase"),
  selectAllBtn: document.getElementById("selectAllBtn"),
  tipo: document.getElementById("tipo"),
  validateBtn: document.getElementById("validateBtn"),
  validationArea: document.getElementById("validationArea"),
  validationContent: document.getElementById("validationContent"),
};

const DATA_SHEET_NAME = "Data";

/*
Normaliza un valor para poder compararlo de forma consistente:
- Convierte a string
- Quita espacios
- Minúsculas
- Reemplaza espacios por _
- Unifica separadores 
*/
function norm(value) {
  return String(value ?? "")
  .trim()
  .toLowerCase()
  .replace(/\s+/g, "_")
  .replace(/\\/g, "/");
}

/*
Obtiene el valor de una fila a partir del nombre de la columna,
comparando los headers de forma normalizada para evitar problemas
de mayúsculas, espacios o separadores.
- Normaliza el nombre del header buscado
- Busca una clave equivalente en el objeto row
- Devuelve el valor asociado o string vacío si no existe
*/
function getRowValue(row, headerName) {
  const wanted = norm(headerName);
  const key = Object.keys(row).find((k) => norm(k) === wanted);
  return key ? row[key] : "";
}

/*
Asigna un valor a una fila usando el nombre de la columna,
normalizando el header para encontrar una clave existente.
- Si la columna ya existe (normalizada), sobreescribe su valor
- Si no existe, crea una nueva columna con el nombre original
*/
function setRowValue(row, headerName, value) {
  const wanted = norm(headerName);
  const key = Object.keys(row).find((k) => norm(k) === wanted);

  if (key) {
    row[key] = value;
  } else {
    row[headerName] = value;
  }
}

/*
Determina si un header corresponde a una columna de control,
usando comparación normalizada para mayor consistencia.
Las columnas de control son columnas especiales que no deben
tratarse como datos de negocio.
*/
function isControlColumn(headerName) {
  const n = norm(headerName);
  return (
    n === norm("# Case") ||
    n === norm("Creado") ||
    n === norm("Estado") ||
    n === norm("Proceso")
  );
}

/*
Escapa HTML para evitar inyección o errores de renderizado
*/
function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/*
Actualiza el texto de estado pricipal de la aplicación
*/
function setStatus(text, kind = "muted") {
  els.status.textContent = text;
  els.status.style.color =
    kind === "ok" ? "#166534" :
    kind === "err" ? "#991b1b" :
    "#475569";
}

/*
Muestra una alerta temporal en pantalla
*/
function notify(message, kind = "info") {
  const div = document.createElement("div");
  div.className = kind === "ok" ? "alert-success" : kind === "err" ? "alert-error" : "alert-info";
  div.style.cssText = "padding:8px 12px;border-radius:6px;margin-bottom:6px;background:#e2e8f0;color:#0f172a;";
  if (kind === "ok") div.style.cssText = "padding:8px 12px;border-radius:6px;margin-bottom:6px;background:#dcfce7;color:#166534;";
  if (kind === "err") div.style.cssText = "padding:8px 12px;border-radius:6px;margin-bottom:6px;background:#fee2e2;color:#991b1b;";
  div.textContent = message;
  els.alertsArea.appendChild(div);

  // Se elimina sola luego de 3.5s
  setTimeout(() => div.remove(), 3500);
}

/*
Habilita o deshabilita los botones principales
*/
function setControlsEnabled(enabled) {
  els.btnCheck.disabled = !enabled;
  els.btnPreview.disabled = !enabled;
  els.btnGenerate.disabled = !enabled;
  els.validateBtn.disabled = !enabled;
  els.btnSaveWorkbook.disabled = !enabled;
}

/*
Genera una clave única para un archivo
Usa la ruta relativa si existe (select folder)
*/
function fileKey(file) {
  return norm(file.webkitRelativePath || file.name);
}

/*
Busca un archivo cuyo nombre termine en un sufijo concreto
*/
function findFileByNameEndsWith(suffix) {
  const wanted = norm(suffix);
  for (const [key, file] of state.files.entries()) {
    if (key.endsWith(wanted)) return file;
  }
  return null;
}

/*
Determina si un valor representa "creado"
*/
function isCreated(value) {
  const s = String(value ?? "").trim().toLowerCase();
  return ["si", "sí", "yes", "true", "1", "x", "creado"].includes(s);
}

/*
Lee las filas de datos desde la hoja de Excel configurada.
- Obtiene la hoja DATA_SHEET_NAME del workbook
- Lanza un error si la hoja no existe
- Convierte la hoja a un array de objetos (una fila = un objeto)
- Usa string vacío como valor por defecto para celdas vacías
*/
function readDataRows() {
  const ws = state.workbook?.Sheets?.[DATA_SHEET_NAME];
  if (!ws) throw new Error(`No existe la hoja "${DATA_SHEET_NAME}" en el Excel.`);

  const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });
  return rows;
}

/*
Obtiene los valores únicos de una columna específica a partir de las filas.
- Extrae el valor de la columna usando comparación normalizada
- Convierte los valores a string y elimina espacios
- Filtra valores vacíos
- Elimina duplicados
- Ordena alfabéticamente el resultado
*/
function getUniqueValues(rows, columName) {
  return [...new Set(
    rows
      .map((r) => String(getRowValue(r, columName)).trim())
      .filter(Boolean)
  )].sort((a, b) => a.localeCompare(b));
}

/*
Genera las opciones de los selects de filtro a partir de los datos cargados.
- Obtiene los valores únicos de Estado y Proceso
- Construye dinámicamente los <option> de cada dropdown
- Escapa los valores para evitar problemas de HTML
- Selecciona el primer valor disponible por defecto
*/
function renderFilterOptionsFromData(rows) {
  const estados = getUniqueValues(rows, "Estado");
  const procesos = getUniqueValues(rows, "Proceso");

  els.estado.innerHTML =
    `<option value="">Todos</option>` +
    estados.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");

  els.tipo.innerHTML =
    `<option value="">Todos</option>` +
    procesos.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");

  if (estados.length) els.estado.value = estados[0];
  if (procesos.length) els.tipo.value = procesos[0];
}

/*
Filtra las filas según los valores seleccionados en los dropdowns.
- Normaliza los valores seleccionados para comparación
- Obtiene Estado y Proceso de cada fila de forma normalizada
- Aplica la lógica de "Todos" o valor vacío como comodín
- Devuelve solo las filas que cumplen ambos filtros
*/
function filterRowsByDropdowns(rows) {
  const wantedEstado = norm(els.estado.value);
  const wantedProceso = norm(els.tipo.value);

  return rows.filter((row) => {
    const rowEstado = norm(getRowValue(row, "Estado"));
    const rowProceso = norm(getRowValue(row, "Proceso"));

    const okEstado = !wantedEstado || wantedEstado === "todos" || rowEstado === wantedEstado;
    const okProceso = !wantedProceso || wantedProceso === "todos" || rowProceso === wantedProceso;

    return okEstado && okProceso;
  });
}

/*
Filtra filas pendientes (no creadas)
*/
function getPendingRows(rows) {
  return rows.filter((r) => !isCreated(getRowValue(r, "Creado")));
}

/*
Renderiza la tabla HTML de registros pendientes
*/
function renderTable(rows) {
  state.visibleRows = rows;
  els.count.textContent = String(rows.length);
  els.pendingSection.style.display = rows.length ? "block" : "none";

  const headers = rows.length ? Object.keys(rows[0]) : [];

  const priority = ["# Case", "Estado", "Proceso", "Creado"];
  const orderedHeaders = [
    ...priority.filter((p) => headers.some((h) => norm(h) === norm(p))),
    ...headers.filter((h) => !priority.some((p) => norm(p) === norm(h)))
  ];

  const uniqueHeaders = orderedHeaders.filter(
    (h, i, arr) => arr.findIndex((x) => norm(x) === norm(h)) === i
  );

  const thead = els.pendingTable.querySelector("thead");
  const tbody = els.pendingTable.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  // Cabecera
  const headRow = document.createElement("tr");
  headRow.innerHTML = `
    <th></th>
    ${uniqueHeaders.map((h) => `<td>${escapeHtml(h)}</td>`).join("")}
  `;
  thead.appendChild(headRow);

  // Filas
  for (const row of rows) {
    const caseValue = String(getRowValue(row, "# Case")).trim();
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><input type="checkbox" data-case="${escapeHtml(caseValue)}"></td>
      ${uniqueHeaders.map((h) => `<td>${escapeHtml(getRowValue(row, h) ?? "")}</td>`).join("")}
    `;

    tbody.appendChild(tr);
  }
}

/*
Obtiene los #case seleccionados
*/
function getSelectedCases() {
  return [...els.pendingTable.querySelectorAll('input[type="checkbox"]:checked')]
    .map(cb => cb.dataset.case)
    .filter(Boolean);
}

/*
Devuelve filas seleccionadas, o todas si no hay selección
*/
function selectedRowsOrVisible(rows) {
  const selected = getSelectedCases();
  if (!selected.length) return rows;
  const set = new Set(selected.map((s) => String(s).trim()));
  return rows.filter((row) => set.has(String(getRowValue(row, "# Case")).trim()));
}

/*
Devuelve el archivo de plantilla PDF correspondiente
*/
function getTemplateFile() {
  const fileName = `templates/pdf/plantilla_${els.estado.value}_${els.tipo.value}.pdf`;
  const file = findFileByNameEndsWith(fileName);
  if (!file) {
    throw new Error(`No encontré la plantilla "${fileName}".`);
  }
  return file;
}

/*
Carga todos los archivos de una carpeta seleccionada por el usuario
Inicializa el estado de la app, encuentra el Excel y prepara la UI
*/
async function loadFolder(files) {
  // Si había un PDF en vista previa activo, se libera su URL para evitar fugas de memoria
  if (state.preview.liveUrl) {
    URL.revokeObjectURL(state.preview.liveUrl);
  }

    /*
    Reinicio completo del estado de preview:
    Se limpia cualquier referencia a PDFs, filas o renderizados anteriores
    */
    state.preview = {
      items: [],  // Registros a previsualizar
      index: 0,  // Índice actual
      row: null,  // Fila actual
      templateBytes: null,  // Bytes del PDF plantilla
      fieldTypes: new Map(),  // Tipos de campos  del PDF
      liveUrl: "",  // URL del PDF vivo
      renderToken: 0  // Token para controlar renders concurrentes
    };

    // Reset visual de la sección de vista previa
    els.previewArea.style.display = "none";
    els.previewSingleFrame.src = "";
    els.previewCounter.textContent = "0/0";
    els.previewCaseTitle.textContent = "Sin selección";

    /*
    Limpieza total del estado relacionado al proyecto cargado anteriormente
    */
    state.files.clear();  // Mapa de archivos
    state.workbook = null;  // Excel cargado 
    state.workbookFile = null;  // Archivo Excel
    state.currentRows = [];  // Filas actuales del Excel
    state.visibleRows = [];  // Filas visibles en la tabla
    state.updatedWorkbookBlob = null;  // Excel modificado
    state.generatedRows = [];
    state.outputDirLabel = "";

    // Limpieza de UI
    els.filesList.innerHTML = "";
    els.validationContent.innerHTML = "";
    els.previewArea.style.display = "none";
    els.resultArea.style.display = "none";
    els.validationArea.style.display = "none";

    /*
    Itera todos los archivos seleccionados:
    - Los guarda en el Map usando una clave normalizada
    - Detecta el archivo registros.xlsx
    */
    for (const file of files) {
      state.files.set(fileKey(file), file);

      // Se identifica el Excel principal
      if (norm(file.name).endsWith("registros.xlsm")) {
        state.workbookFile = file;
      }
    }

    // Si no se encontró el Excel obligatorio → Error
    if (!state.workbookFile) {
      throw new Error("No encontré data/registros.xlsx dentro de la carpeta elegida.");
    }

    // Se lee el archivo Excel como ArrayBuffer y se parsea usando XLSX
    const wbBuffer = await state.workbookFile.arrayBuffer();
    state.workbook = XLSX.read(wbBuffer, { type: "array" });

    // Se generan los filtros desde la hoja Data
    const allRows = readDataRows();
    renderFilterOptionsFromData(allRows);
    state.currentRows = allRows;

    // Se habilitan los controles principales
    setControlsEnabled(true);

    // feedback visual
    els.folderStatus.textContent = `Carpeta cargada: ${files.length} archivo(s).`;
    setStatus("Proyecto cargado correctamente.", "ok");
    notify("Carpeta cargada.", "ok");

    // Se ejecuta una primera validación de registros pendientes
    await checkRecords();
  }

/*
Verifica la hoja actualmente seleccionada y renderiza los registros pendientes
*/
async function checkRecords() {
  try {
    const rows = readDataRows();
    state.currentRows = rows;

    const filteredByDropdowns = filterRowsByDropdowns(rows);
    const pending = getPendingRows(filteredByDropdowns);

    renderTable(pending);

    setStatus(`Data; ${pending.length} registro(s) pendientes.`, "ok");
    notify("Comprobación terminada.", "ok");
  } catch (err) {
    setStatus(String(err.message || err), "err");
    notify(String(err.message || err), "err");
    throw err;
  }
}

/*
Crea una URL temporal (blob URL) a partir de bytes PDF
*/
function blobUrlFromBytes(bytes) {
  return URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
}

/*
Retrasa la ejecución de una función hasta que el usuario deje de escribir por X milisegundos
*/
function debounce(fn, delay = 250) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/*
Obtiene los tipos de campos existentes en la plantilla PDF
(ej: PDFTextField, PDFCheckBox, etc.)
*/
async function getPdfFieldTypes(templateBytes) {
  const pdfDoc = await PDFDocument.load(templateBytes);
  const form = pdfDoc.getForm();
  const map = new Map();

  // Se normaliza el nombre del campo para coincidir con Excel
  for (const field of form.getFields()) {
    map.set(norm(field.getName()), field.constructor.name);
  }

  return map;
}

/*
Cierra el modal de vista previa editable y limpia recursos asociados
*/
function closePreviewModal() {
  els.previewModal.style.display = "none";
  els.previewModalBody.innerHTML = "";

  // Liberación del PDF en vivo
  if (state.preview.liveUrl) {
    URL.revokeObjectURL(state.preview.liveUrl);
    state.preview.liveUrl = "";
  }

  // Reset del estado de preview
  state.preview.row = null;
  state.preview.templateBytes = null;
  state.preview.fieldTypes = new Map();
  state.preview.renderToken = 0;
}

/*
Construye dinámicamente el editor de campos para la vista previa editable.
A partir de una fila (row del Excel), crea inputs HTML que están sincronizados en tiempo real con el PDF
*/
function buildPreviewEditor(row) {
  // Contenedor principal donde se colocarán todos los campos editables
  const container = document.createElement("div");
  container.className = "preview-fields";

  /*
  Se obtienen las claves (columnas) del registro:
  - Se excluyen campos de control (#case, creado)
  - Se incluyen SOLO los campos que existen en la plantilla PDF 
  */
  const keys = Object.keys(row).filter((key) => {
    const k = norm(key);
    return (
      k !== norm("# Case") &&  // No se edita el identificador
      k !== norm("Creado") &&  // no se edita el estado de creación
      k !== norm("Estado") &&
      k !== norm("Proceso") &&
      state.preview.fieldTypes.has(k)  // Debe existir en el PDF
    );
  });

  // Si no hay campos editables, se muestra un mensaje informativo
  if (!keys.length) {
    container.innerHTML = "<p>No hay campos editables para este registro.</p>";
    return container;
  }

  // Para cada campo editable:
  // - Se crea una fila visual
  // - Se decide el tipo de input según el tipo de campo PDF
  for (const key of keys) {
    const k = norm(key);
    // Tipo de campo PDF (ej: PDFTextField, PDFCheckBox, etc.)
    const fieldType = state.preview.fieldTypes.get(k);
    // Contenedor individual de cada campo
    const wrap = document.createElement("div");
    wrap.className = "preview-field";

    // Texto usado para búsquedas en el editor
    wrap.dataset.search = `${key} ${fieldType}`;

    // Etiqueta del campo (nombre de la columna Excel)
    const label = document.createElement("label");
    label.textContent = key;
    wrap.appendChild(label);

    /*
    Si el campo PDF es un checkbox:
    - Se crea un input type="checkbox"
    - Se traduce el valor del Excel a boolean
    */
    if (fieldType === "PDFCheckBox") {
      const input = document.createElement("input");
      input.type = "checkbox";
      // El checkbox se activa si el valor del excel indica "SI/Yes"
      input.checked = isCreated(row[key]);

      // Al cambiar el checkbox:
      // - Se actualiza la fila en memoria
      // - Se refresca el PDF en vivo
      input.addEventListener("change", () => {
        row[key] = input.checked ? "SI" : "";
        updateLivePreview();
      });

      wrap.appendChild(input);
    }
    /*
    Para cualquier otro tipo de campo:
    - Se usa input de Texto 
    */
    else {
      const input = document.createElement("input");
      input.type = "text";

      // Valor inicial desde Excel
      input.value = row[key] ?? "";

      /*
      Evento input con debounce:
      - Evita regenerar el PDF en cada tecla
      - Espera 180ms tras dejar de escribir
      */
      input.addEventListener(
        "input",
        debounce(() => {
          row[key] = input.value;
          updateLivePreview();
        }, 180)
      );

      wrap.appendChild(input);
    }
    // Se añade el campo al contenedor principal
    container.appendChild(wrap);
  }
  // Se devuelve el editor completamente armado
  return container;
}

/*
Filtra los campos del editor según el texto ingresado por el usuario.
Oculta los campos que no coincidad con la búsqueda
*/
function filterPreviewFields(query) {
  // Se normaliza el texto de búsqueda
  const q = norm(query).replace(/\s+/g, "_");

  // Se recorren todos los campos del editor
  document.querySelectorAll("#previewEditorFields .preview-field").forEach((el) => {
    const text = norm(el.dataset.search || "");
    // Se muestra u oculta según coincidencia
    el.style.display = text.includes(q) ? "" : "none";
  });
}

/*
Regenera el PDF en tiempo real usando los valores actuales del editor.
Esta función es el corazón de la "vista previa en vivo"
*/
async function updateLivePreview() {
  // Si no hay registro o plantilla cargada, no hace nada
  if (!state.preview.row || !state.preview.templateBytes) return;

  // Se incrementa el token para invalidar renders anteriores
  const token = ++state.preview.renderToken;

  // Iframe donde se muestra el PDF
  const iframe = document.getElementById("livePreviewFrame");
  if (!iframe) return;

  // Se genera el PDF con los valoresactuales (No flatten)
  const pdfBytes = await fillPdf(state.preview.templateBytes, state.preview.row, {
    flatten: false
  });

  // Se crea una URL temporal del PDF
  const url = blobUrlFromBytes(pdfBytes);

  /*
  Control de concurrencias:
  Si mientras se generaba este PDF hubo otro cambio,
  se descarta este render.
  */
  if (token !== state.preview.renderToken) {
    URL.revokeObjectURL(url);
    return;
  }

  // Se libera el PDF anterior si existia
  if (state.preview.liveUrl) {
    URL.revokeObjectURL(state.preview.liveUrl);
  }

  // Se actualiza el iframe con el nuevo PDF
  state.preview.liveUrl = url;
  iframe.src = url;
}

/*
Abre el modal de edición avanzada con:
- PDF en Vivo
- Editor de campos sincronizados
*/
async function openEditablePreview(row) {
  // Se obtiene la plantilla PDF correcta
  const templateFile = getTemplateFile();
  const templateBytes = await templateFile.arrayBuffer();
  // Se obtienen los tipos de campos del PDF
  const fieldTypes = await getPdfFieldTypes(templateBytes);

  // Se inicializa ele stado de preview
  state.preview.row = row;
  state.preview.templateBytes = templateBytes;
  state.preview.fieldTypes = fieldTypes;
  state.preview.renderToken = 0;

  // Se muestra el modal
  els.previewModal.style.display = "grid";
  // Se inyecta la estructura HTML del modal
  els.previewModalBody.innerHTML = `
    <div class="preview-modal-layout">
      <div class="preview-pdf-panel">
        <h3>Vista previa PDF</h3>
        <iframe id="livePreviewFrame"></iframe>
      </div>

      <div class="preview-editor-panel">
        <h3>Editar registro #${escapeHtml(String(row["#case"] ?? ""))}</h3>
        <input id="fieldSearchInput" class="preview-search" type="text" placeholder="Buscar campo..." />
        <div id="previewEditorFields"></div>
        <div class="button-row" style="margin-top:12px;">
          <button id="applyPreviewChanges" class="main-btn" type="button">Aplicar cambios</button>
          <button id="closePreviewFromEditor" class="main-btn" type="button">Cerrar</button>
        </div>
      </div>
    </div>
  `;

  // Se construye e inserta el editor dinámico
  const editorHost = document.getElementById("previewEditorFields");
  editorHost.appendChild(buildPreviewEditor(row));

  // Búsqueda de campos en tiempo real
  const fieldSearchInput = document.getElementById("fieldSearchInput");
  fieldSearchInput.addEventListener("input", () => {
    filterPreviewFields(fieldSearchInput.value);
  });
  filterPreviewFields("");

  /*
  Botón "Aplicar cambios"

  - Refresca la tabla principal
  - Mantiene los cambios en memoria (Excel)
  */
  document.getElementById("applyPreviewChanges").addEventListener("click", () => {
    renderTable(getPendingRows(state.currentRows));
    notify("Cambios aplicados en memoria y en el Excel.", "ok");
    closePreviewModal();
  });

  // Botón cerrar
  document.getElementById("closePreviewFromEditor").addEventListener("click", () => {
    closePreviewModal();
  });
  // Render inicial del PDF
  await updateLivePreview();
}

/*
Rellena un PDF a partir de una fila de datos (Excel/JSON).
- Carga el PDF plantilla desde bytes
- Mapea los campos del formulario PDF por nombre normalizado
- Recorre las columnas de la fila y llena los campos correspondientes
- Soporta campos de texto, checkboxes y selects
- Permite aplanar el formulario (flatten) opcionalmente
- Devuelve los bytes del PDF generado
*/
async function fillPdf(templateBytes, row, { flatten = false } = {}) {
  const pdfDoc = await PDFDocument.load(templateBytes);
  const form = pdfDoc.getForm();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);

  // Mapa de campos del PDF indexados por nombre normalizado
  const fieldMap = new Map();
  for (const field of form.getFields()) {
    fieldMap.set(norm(field.getName()), field);
  }

  // Recorre las columnas de la fila de datos
  for (const [excelKey, rawValue] of Object.entries(row)) {
    const k = norm(excelKey);

    // Ignora columnas de control
    if (
      k === norm("# Case") ||
      k === norm("Creado") ||
      k === norm("Estado") ||
      k === norm("Proceso")
    ) continue;

    const field = fieldMap.get(k);
    if (!field) continue;

    const value = rawValue == null ? "" : String(rawValue).trim();

    try {
      // Campos de texto
      if (typeof field.setText === "function") {
        field.setText(value);
      // Checkboxes
      } else if (typeof field.check === "function" && typeof field.uncheck === "function") {
        const on = ["si", "sí", "yes", "true", "1", "x"].includes(value.toLowerCase());
        on ? field.check() : field.uncheck();
      // Selects / dropdowns
      } else if (typeof field.select === "function") {
        try { field.select(value); } catch {}
      }
    } catch (err) {
      console.warn("Error llenando campo:", excelKey, err);
    }
  }

  // Actualiza las apariencias visuales de los campos
  try {
    form.updateFieldAppearances(font);
  } catch (err) {
    console.warn("No se pudieron actualizar apariencias:", err);
  }

  // Convierte el formulario en contenido estático si se solicita
  if (flatten) {
    try { form.flatten(); } catch {}
  }

  return await pdfDoc.save({ updateFieldAppearances: true });
}

/*
Escribe un PDF en la carpeta seleccionada por el usuario.
- Crea (o sobrescribe) el archivo indicado
- Escribe los bytes como application/pdf
*/
async function writePdfToSelectedFolder(folderHandle, filename, pdfBytes) {
  const fileHandle = await folderHandle.getFileHandle(filename, { create: true });
  const writable = await fileHandle.createWritable();
  await writable.write(new Blob([pdfBytes], { type: "application/pdf" }));
  await writable.close();
}

/*
Inicializa la vista previa de registros seleccionados.
- Obtiene la plantilla PDF
- Usa filas seleccionadas o visibles
- Inicializa el estado de preview
- Renderiza la primera previsualización
*/
async function previewRecords() {
  try {
    const templateFile = getTemplateFile();
    const templateBytes = await templateFile.arrayBuffer();
    const rows = selectedRowsOrVisible(state.visibleRows);

    if (!rows.length) {
      notify("No hay registros para previsualizar.", "err");
      return;
    }

    state.preview.items = rows;
    state.preview.index = 0;
    state.preview.templateBytes = templateBytes;

    els.previewArea.style.display = "block";
    await renderPreviewAt(0);

    setStatus("Vista previa lista.", "ok");
  } catch (err) {
    setStatus(String(err.message || err), "err");
    notify(String(err.message || err), "err");
  }
}

/*
Renderiza la vista previa de un registro específico.
- Genera el PDF sin aplanar
- Crea un ObjectURL para visualización
- Actualiza controles de navegación y UI
- Permite abrir edición del registro actual
*/
async function renderPreviewAt(index) {
  const row = state.preview.items[index];
  if (!row) return;

  state.preview.index = index;

  const pdfBytes = await fillPdf(state.preview.templateBytes, row, { flatten: false });
  const url = blobUrlFromBytes(pdfBytes);

  // Limpia la URL anterior si existe
  if (state.preview.liveUrl) {
    URL.revokeObjectURL(state.preview.liveUrl);
  }

  state.preview.liveUrl = url;

  // Actualiza la UI de la vista previa
  els.previewSingleFrame.src = url;
  els.previewCounter.textContent = `${index + 1}/${state.preview.items.length}`;
  els.previewCaseTitle.textContent = `#${String(row["#case"] ?? "").trim()}`;

  els.previewPrevBtn.disabled = index <= 0;
  els.previewNextBtn.disabled = index >= state.preview.items.length - 1;

  els.editCurrentPreviewBtn.onclick = () => {
    openEditablePreview(row);
  };
}

/*
Renderiza la lista de archivos PDF generados.
- Muestra el área de resultados
- Limpia la lista previa
- Agrega un item por cada archivo generado
*/
function renderGeneratedList(items) {
  els.resultArea.style.display = "block";
  els.filesList.innerHTML = "";

  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = `${item.caseValue} → ${item.filename}`;
    els.filesList.appendChild(li);
  }
}

/*
Construye un archivo Excel con el resumen de los PDFs generados.
- Valida que existan registros generados
- Crea un workbook y una hoja desde los datos generados
- Define headers explícitos y valores por defecto
- Devuelve un Blob listo para descargar o guardar
*/
function buildGeneratedExcelBlob() {
  if (!state.generatedRows.length) {
    throw new Error("No hay registros generados para exportar.");
  }

  const wb = XLSX.utils.book_new();

  const ws = XLSX.utils.json_to_sheet(state.generatedRows, {
    header: ["# Case", "Creado", "File Name", "Saved in"],
    defval: ""
  });

  XLSX.utils.book_append_sheet(wb, ws, "Generados");

  const out = XLSX.write(wb, { bookType: "xlsx", type: "array" });

  return new Blob([out], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  });
}

/*
Guarda en disco el Excel de registros generados.
- Usa File System Access API si está disponible
- Usa descarga tradicional como fallback
- Maneja errores y notificaciones al usuario
*/
async function saveWorkbookToDisk() {
  try {
    const blob = buildGeneratedExcelBlob();

    if ("showSaveFilePicker" in window) {
      const handle = await window.showSaveFilePicker({
        suggestedName: "generados.xlsx",
        types: [{
          description: "Excel",
          accept: {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"]
          }
        }]
      });

      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
    } else {
      // Fallback para navegadores sin File System Access API
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "generados.xlsx";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    notify("Excel exportado correctamente.", "ok");
  } catch (err) {
    setStatus(String(err.message || err), "err");
    notify(String(err.message || err), "err");
  }
}

/*
Genera los PDFs a partir de la plantilla y las filas seleccionadas.
- Carga la plantilla PDF
- Usa filas seleccionadas o visibles
- Genera y guarda cada PDF (en carpeta o por descarga)
- Marca la fila como creada
- Actualiza el resumen de generación
- Refresca la UI y muestra notificaciones
*/
async function generatePdfs() {
  try {
    const templateFile = getTemplateFile();
    const templateBytes = await templateFile.arrayBuffer();
    const rows = selectedRowsOrVisible(state.visibleRows);

    if (!rows.length) {
      notify("No hay registros para generar.", "err");
      return;
    }

    const generated = [];
    const savedInLabel = state.outputDirLabel || "Descargas del navegador";

    for (const row of rows) {
      const caseValue = String(getRowValue(row, "# Case")).trim();
      const pdfBytes = await fillPdf(templateBytes, row, { flatten: true });
      const filename = `${caseValue}-${els.tipo.value}-${els.estado.value}-${new Date().toISOString().slice(0, 10)}.pdf`;

      // Guarda el PDF en carpeta seleccionada o descarga directa
      if (state.outputDirHandle) {
        await writePdfToSelectedFolder(state.outputDirHandle, filename, pdfBytes);
      } else {
        const pdfBlob = new Blob([pdfBytes], { type: "application/pdf" });
        const url = URL.createObjectURL(pdfBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }

      // Marca la fila como creada
      setRowValue(row, "Creado", "SI");

      // Fila de exportación para el Excel resumen
      const exportRow = {
        "# Case": caseValue,
        "Creado": "SI",
        "File Name": filename,
        "Saved in": savedInLabel
      };

      // Actualiza o inserta el registro generado
      const existingIndex = state.generatedRows.findIndex(
        (r) => String(r["# Case"] ?? "").trim() === caseValue
      );

      if (existingIndex >= 0) {
        state.generatedRows[existingIndex] = exportRow;
      } else {
        state.generatedRows.push(exportRow);
      }

      generated.push({ caseValue, filename });
    }

    // Actualiza resultados y UI
    renderGeneratedList(generated);
    renderTable(getPendingRows(filterRowsByDropdowns(state.currentRows)));

    notify(`Generados ${generated.length} archivo(s).`, "ok");
    setStatus(`Generados ${generated.length} archivo(s).`, "ok");
  } catch (err) {
    setStatus(String(err.message || err), "err");
    notify(String(err.message || err), "err");
  }
}

/*
Valida la correspondencia entre los campos del Excel y los campos del PDF plantilla.
- Carga la plantilla PDF
- Obtiene los nombres de los campos del formulario PDF
- Normaliza los nombres para comparación consistente
- Obtiene los headers del Excel (ignorando columnas de control)
- Detecta campos que faltan en el PDF o en el Excel
- Muestra un resumen de la validación en la UI
*/
async function validateTemplate() {
  try {
    const templateFile = getTemplateFile();
    const templateBytes = await templateFile.arrayBuffer();
    const pdfDoc = await PDFDocument.load(templateBytes);

    // Campos del PDF normalizados
    const pdfFieldNames = pdfDoc.getForm().getFields().map(f => f.getName());
    const pdfNorm = pdfFieldNames.map(norm);

    // Filas actuales del Excel (o lectura directa si no hay estado cargado)
    const rows = state.currentRows.length ? state.currentRows : readCurrentSheetRows();
    const headers = rows.length ? Object.keys(rows[0]) : [];

    // Campos del Excel (sin columnas de control)
    const excelFields = headers
      .filter((h) => !isControlColumn(h))
      .map(norm);

    // Diferencias entre Excel y PDF
    const missingInPdf = excelFields.filter(h => !pdfNorm.includes(h));
    const extraInPdf = pdfNorm.filter(h => !excelFields.includes(h));

    // Renderiza el resultado de la validación
    els.validationArea.style.display = "block";
    els.validationContent.innerHTML = `
      <p><strong>Campos en Excel:</strong> ${excelFields.length}</p>
      <p><strong>Campos en PDF:</strong> ${pdfNorm.length}</p>
      <p><strong>Faltan en PDF:</strong> ${missingInPdf.length ? missingInPdf.join(", ") : "ninguno"}</p>
      <p><strong>Faltan en Excel:</strong> ${extraInPdf.length ? extraInPdf.join(", ") : "ninguno"}</p>
    `;

    notify("Validación completada.", "ok");
    setStatus("Validación terminada.", "ok");
  } catch (err) {
    setStatus(String(err.message || err), "err");
    notify(String(err.message || err), "err");
  }
}

/*
Asocia todos los eventos de la interfaz de usuario.
- Carga de carpeta del proyecto
- Acciones principales: validar, previsualizar, generar PDFs
- Filtros y búsqueda
- Navegación de vista previa
- Selección de carpeta de salida
*/
function attachEvents() {
  // Selector de carpeta del proyecto
  els.btnLoadFolder.addEventListener("click", () => els.folderInput.click());

  els.folderInput.addEventListener("change", async () => {
    const files = [...els.folderInput.files];
    if (!files.length) return;

    try {
      await loadFolder(files);
    } catch (err) {
      setControlsEnabled(false);
      setStatus(String(err.message || err), "err");
      notify(String(err.message || err), "err");
    }
  });

  // Acciones principales
  els.btnCheck.addEventListener("click", async () => {
    await checkRecords();
  });

  els.btnPreview.addEventListener("click", async () => {
    await previewRecords();
  });

  els.btnGenerate.addEventListener("click", async () => {
    await generatePdfs();
  });

  els.validateBtn.addEventListener("click", async () => {
    await validateTemplate();
  });

  els.btnSaveWorkbook.addEventListener("click", async () => {
    await saveWorkbookToDisk();
  });

  // Filtros por dropdown
  els.estado.addEventListener("change", async () => {
    if (!state.workbook) return;
    await checkRecords();
  });

  els.tipo.addEventListener("change", async () => {
    if (!state.workbook) return;
    await checkRecords();
  });

  // Búsqueda por # Case
  els.searchCase.addEventListener("input", () => {
    const q = els.searchCase.value.trim().toLowerCase();
    const filtered = state.visibleRows.filter((r) => String(getRowValue(r, "# Case")).toLowerCase().includes(q));
    renderTable(filtered);
  });

  // Selección masiva de registros
  els.selectAllBtn.addEventListener("click", () => {
    [...els.pendingTable.querySelectorAll('input[type="checkbox"]')].forEach(cb => cb.checked = true);
  });

  // Navegación de vista previa
  els.previewPrevBtn.addEventListener("click", async () => {
    if (state.preview.index > 0) {
      await renderPreviewAt(state.preview.index - 1);
    }
  });

  els.previewNextBtn.addEventListener("click", async () => {
    if (state.preview.index < state.preview.items.length - 1) {
      await renderPreviewAt(state.preview.index + 1);
    }
  });

  // Cierre del modal de vista previa
  els.closePreviewModal.addEventListener("click", () => {
    closePreviewModal();
  });

  els.previewModal.addEventListener("click", (e) => {
    if (e.target === els.previewModal) {
      closePreviewModal();
    }
  });

  // Selección de carpeta de salida
  els.btnPickOutput.addEventListener("click", async () => {
    try {
      state.outputDirHandle = await window.showDirectoryPicker();
      state.outputDirLabel = state.outputDirHandle.name || "Carpeta seleccionada";
      notify("Carpeta de salida seleccionada.", "ok");
      setStatus("Carpeta de salida lista.", "ok");
    } catch (err) {
      notify("No se seleccionó carpeta de salida.", "err");
    }
  });

}

// Inicialización
attachEvents();
setControlsEnabled(false);
setStatus("Carga la carpeta del proyecto para comenzar.");
})();