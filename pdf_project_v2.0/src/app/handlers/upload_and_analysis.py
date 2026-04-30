"""
src/app/handlers/upload_and_analysis.py
----------------------------------------
Callbacks para upload de PDF y análisis principal.
- Soporta múltiples archivos en paralelo.
- Genera overlays con colores semánticos por tipo de bloque.
- Almacena doc-context por doc_id para acceso multi-documento.
"""

import base64
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import dash
from dash import Input, Output, State

from src.detection.pdf_type_detector import PDFTypeDetector
from src.ingest.storage import StorageManager
from src.ingest.uploader import IngestManager
from src.metadata.document_store import DocumentStore
from src.visualization.overlay import OverlayGenerator
from src.logs.logger import LogManager
from src.utils.doc_enrichment import build_doc_context


def register_callbacks_02(app, controller, embedder=None):
    ingest      = IngestManager()
    storage     = StorageManager()
    log_mgr     = LogManager()
    detector    = PDFTypeDetector(log_mgr=log_mgr)
    overlay_gen = OverlayGenerator()
    store       = DocumentStore()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _as_list(v):
        if v is None:      return []
        if isinstance(v, list): return v
        return [v]

    def _build_options(items):
        return [
            {"label": i.get("file_name", i["doc_id"]), "value": i["doc_id"]}
            for i in _as_list(items)
            if isinstance(i, dict) and i.get("doc_id")
        ]

    def _unique(existing, new_items):
        merged, seen = [], set()
        for item in _as_list(existing) + _as_list(new_items):
            if not isinstance(item, dict): continue
            did = item.get("doc_id")
            if not did or did in seen: continue
            seen.add(did); merged.append(item)
        return merged

    def _first_preview(doc_ctx):
        if not isinstance(doc_ctx, dict): return dash.no_update
        for ctx in doc_ctx.values():
            if not isinstance(ctx, dict): continue
            for ov in (ctx.get("overlays") or []):
                path = ov.get("path")
                if path:
                    try:
                        with open(path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        return f"data:image/png;base64,{b64}"
                    except Exception:
                        continue
        return dash.no_update

    # ── sync dropdowns cuando cambia upload-store ────────────────────────────

    @app.callback(
        [Output("analysis-target", "options"),
         Output("analysis-target", "value")],
        Input("upload-store", "data"),
        prevent_initial_call=True,
    )
    def _sync_analysis_target(upload_ctx):
        opts = _build_options(_as_list(upload_ctx))
        return opts, (opts[0]["value"] if opts else None)

    @app.callback(
        [Output("visualization-pdf-selector", "options"),
         Output("visualization-pdf-selector", "value")],
        Input("upload-store", "data"),
        prevent_initial_call=True,
    )
    def _sync_viz_selector(upload_ctx):
        opts = _build_options(_as_list(upload_ctx))
        return opts, (opts[0]["value"] if opts else None)

    # ── callback principal: upload + análisis ─────────────────────────────────

    @app.callback(
        [
            Output("upload-store", "data"),
            Output("doc-context", "data"),
            Output("summary-output", "children"),
            Output("pdf-preview", "src"),
            Output("download-visualization-btn", "disabled"),
        ],
        [
            Input("upload-pdf", "contents"),
            Input("run-analysis", "n_clicks"),
        ],
        [
            State("upload-pdf", "filename"),
            State("upload-store", "data"),
            State("analysis-target", "value"),
            State("fast-mode", "value"),
            State("doc-context", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_upload_and_analysis(
        contents, n_clicks, filenames,
        upload_ctx, selected_doc_id, fast_mode, current_doc_ctx
    ):
        triggered = (dash.callback_context.triggered[0]["prop_id"].split(".")[0]
                     if dash.callback_context.triggered else None)

        # ── UPLOAD ────────────────────────────────────────────────────────────
        if triggered == "upload-pdf":
            new_items = []
            for c, fn in zip(_as_list(contents), _as_list(filenames)):
                if not c or not fn: continue
                try:
                    _, enc = c.split(",", 1)
                    saved   = ingest.save_uploaded_file(io.BytesIO(base64.b64decode(enc)), fn)
                    pdf_type = detector.detect(saved["path"])
                    new_items.append({
                        "doc_id":    saved["doc_id"],
                        "file_name": fn,
                        "file_path": saved["path"],
                        "pdf_type":  pdf_type,
                        "status":    "uploaded",
                    })
                except Exception as e:
                    log_mgr.log({"step": "UPLOAD", "status": "error",
                                 "filename": fn, "error_message": str(e)})

            all_items = _unique(upload_ctx, new_items)
            return (all_items, dash.no_update,
                    f"✅ {len(new_items)} archivo(s) cargado(s)" if new_items else "Sin archivos nuevos",
                    dash.no_update, True)

        # ── ANALYSIS ──────────────────────────────────────────────────────────
        if triggered == "run-analysis":
            items     = _as_list(upload_ctx)
            item_map  = {i["doc_id"]: i for i in items
                         if isinstance(i, dict) and i.get("doc_id") and i.get("file_path")}
            selected  = [s for s in _as_list(selected_doc_id) if s in item_map]

            if not item_map:
                return dash.no_update, dash.no_update, "⚠️ Sube un PDF primero.", dash.no_update, True
            if not selected:
                return dash.no_update, dash.no_update, "⚠️ Selecciona archivo(s) para analizar.", dash.no_update, True

            from src.utils.image import render_page_to_image

            results = dict(current_doc_ctx or {})  # preservar documentos ya procesados

            def _process(target):
                doc_id    = target["doc_id"]
                file_path = target["file_path"]
                file_name = target["file_name"]
                pdf_type  = target.get("pdf_type")
                try:
                    result   = controller.process(file_path, file_name, doc_id, fast_mode=bool(fast_mode))
                    result   = result if isinstance(result, dict) else {}
                    pages    = result.get("pages", []) or []
                    mode     = result.get("processing_mode") or ("ocr" if pdf_type == "scanned" else "native")

                    # Generar overlays página por página
                    overlays = result.get("overlays") or []
                    if not overlays:
                        for p in pages:
                            if not isinstance(p, dict): continue
                            pn = p.get("page_number")
                            if pn is None: continue
                            blocks = p.get("blocks") or []
                            try:
                                img_path = storage.page_cache_path(doc_id, pn)
                                render_page_to_image(file_path, pn, img_path)
                                ov_path  = overlay_gen.render_page_overlay(
                                    img_path, blocks, doc_id, pn,
                                    p.get("width", 612), p.get("height", 792),
                                )
                                if ov_path:
                                    overlays.append({"page": pn, "path": ov_path})
                            except Exception as e:
                                log_mgr.log({"step": "OVERLAY", "status": "error",
                                             "file_id": doc_id, "error_message": str(e)})

                    # Construir doc_ctx enriquecido
                    doc_ctx = build_doc_context(
                        doc_id=doc_id,
                        file_name=file_name,
                        file_path=file_path,
                        pages=pages,
                        overlays=overlays,
                        processing_mode=mode,
                    )
                    doc_ctx["report"] = {
                        "pages":  len(pages),
                        "blocks": len(doc_ctx.get("classified_blocks", [])),
                        "fields": len(doc_ctx.get("fields", [])),
                    }
                    try:
                        doc_ctx["saved_path"] = store.save_document(doc_ctx)
                    except Exception:
                        doc_ctx["saved_path"] = None

                    return doc_id, doc_ctx

                except Exception as e:
                    import traceback
                    log_mgr.log(
                        {
                            "step": "PROCESS_PDF", "status": "error",
                            "file_id": doc_id, "filename": file_name,
                            "error_message": f"{e}\n{traceback.format_exc()}"
                        }
                    )
                    return doc_id, None

            with ThreadPoolExecutor(max_workers=min(4, len(selected))) as ex:
                futures = [ex.submit(_process, item_map[did]) for did in selected]
                for fut in as_completed(futures):
                    did, res = fut.result()
                    if did and res:
                        results[did] = res

            if not results:
                return dash.no_update, dash.no_update, "❌ No se procesó ningún PDF.", dash.no_update, True

            n_new = sum(1 for d in selected if d in results)
            summary = (
                f"✅ {n_new} documento(s) procesado(s). "
                f"Total en sesión: {len(results)}."
            )
            return dash.no_update, results, summary, _first_preview(results), False

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
