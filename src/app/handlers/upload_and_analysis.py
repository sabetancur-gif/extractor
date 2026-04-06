
"""
src/app/handlers/upload_and_analysis.py
----------------------------------------
Callbacks para upload de PDF y análisis principal (procesamiento, resumen, preview).
"""

# STDLIB
import base64
import io
from datetime import datetime
import threading

# THIRDPARTY
import dash
from dash import Input, Output, State


# FIRSTPARTY
from src.detection.pdf_type_detector import PDFTypeDetector
from src.ingest.storage import StorageManager
from src.ingest.uploader import IngestManager
from src.metadata.document_store import DocumentStore
from src.visualization.overlay import OverlayGenerator
from src.logs.logger import LogManager


def register_callbacks_02(app, controller, embedder=None):
    # Callback para poblar el nuevo dropdown analysis-doc-selector SOLO con los documentos procesados (doc-context)
    @app.callback(
        [
            Output("analysis-doc-selector", "options"),
            Output("analysis-doc-selector", "value"),
        ],
        [
            Input("doc-context", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_analysis_doc_selector(doc_ctx):
        if not doc_ctx or not isinstance(doc_ctx, dict):
            return [], None
        options = []
        for doc_id, ctx in doc_ctx.items():
            if isinstance(ctx, dict):
                label = ctx.get("file_name", doc_id)
            else:
                label = str(doc_id)
            options.append({"label": label, "value": doc_id})
        value = options[0]["value"] if options else None
        return options, value
    # Callback para actualizar el dropdown de PDF Analysis SOLO con los documentos procesados (doc-context)
    @app.callback(
        [
            Output("analysis-target", "options", allow_duplicate=True),
            Output("analysis-target", "value", allow_duplicate=True),
        ],
        [
            Input("doc-context", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_analysis_target_from_processed(doc_ctx):
        if not doc_ctx or not isinstance(doc_ctx, dict):
            return [], None
        options = []
        for doc_id, ctx in doc_ctx.items():
            if isinstance(ctx, dict):
                label = ctx.get("file_name", doc_id)
            else:
                label = str(doc_id)
            options.append({"label": label, "value": doc_id})
        value = [options[0]["value"]] if options else None
        return options, value
    """
    Registra callbacks para:
        - Actualizar selector de PDF para visualización.
        - Procesar archivos subidos y generar análisis/resumen/preview.
    Relacionado con IDs: upload-pdf, run-analysis, visualization-pdf-selector, summary-output, pdf-preview, analysis-target, download-visualization-btn, etc.
    """
    # Callback para actualizar visualization-pdf-selector SOLO con los documentos procesados (doc-context)
    @app.callback(
        [
            Output("visualization-pdf-selector", "options"),
            Output("visualization-pdf-selector", "value"),
        ],
        [
            Input("doc-context", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_visualization_selector(doc_ctx):
        if not doc_ctx or not isinstance(doc_ctx, dict):
            return [], None
        options = []
        for doc_id, ctx in doc_ctx.items():
            if isinstance(ctx, dict):
                label = ctx.get("file_name", doc_id)
            else:
                label = str(doc_id)
            options.append({"label": label, "value": doc_id})
        value = options[0]["value"] if options else None
        return options, value

    ingest = IngestManager()
    storage = StorageManager()
    log_mgr = LogManager()
    detector = PDFTypeDetector(log_mgr=log_mgr)
    overlay_gen = OverlayGenerator()
    store = DocumentStore()

    @app.callback(
        [
            Output("upload-store", "data"),        # Uploaded files context
            Output("doc-context", "data"),         # Contexto del documento (Analisis)
            Output("summary-output", "children"),  # Resumen corto del documento
            Output("pdf-preview", "src"),          # PDF Preview del analisis
            Output("analysis-target", "options"),  # Fields opciones para el dropdown
            Output("analysis-target", "value"),    # Valores de los Fields dropdown
            Output("download-visualization-btn", "disabled"),
        ],
        [
            Input("upload-pdf", "contents"),       # PDF upload
            Input("run-analysis", "n_clicks"),     # Run analysis button (create visualization)
        ],
        [
            State("upload-pdf", "filename"),       # Uploaded filenames
            State("upload-store", "data"),         # Uploaded files context
            State("analysis-target", "value"),     # Selected doc to analyze
            State("fast-mode", "value"),           # Fast mode checkbox
        ],
        prevent_initial_call=True,
    )
    def handle_upload_and_analysis(contents, n_clicks, filenames, upload_ctx, selected_doc_id, fast_mode):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        # --------- Subida de archivos ---------
        if triggered_id == "upload-pdf":
            if not contents:
                raise dash.exceptions.PreventUpdate

            if not isinstance(contents, list):
                contents, filenames = [contents], [filenames]

            items = [] if not upload_ctx else (upload_ctx if isinstance(upload_ctx, list) else [upload_ctx])

            for c, fn in zip(contents, filenames):
                header, encoded = c.split(",", 1)
                file_bytes = io.BytesIO(base64.b64decode(encoded))
                saved = ingest.save_uploaded_file(file_bytes, fn)
                pdf_type = detector.detect(saved["path"])
                print(f"pdf_type: {pdf_type}")
                items.append(
                    {
                        "doc_id": saved["doc_id"],
                        "file_name": fn,
                        "file_path": saved["path"],
                        "pdf_type": pdf_type,
                        "status": "uploaded",
                    }
                )
                storage.clear_cache(saved["doc_id"])
                log_mgr.log({
                    "timestamp": datetime.now().isoformat(),
                    "file_id": saved["doc_id"],
                    "filename": saved["filename"],
                    "step": "UPLOAD",
                    "page_number": None,
                    "pages_total": None,
                    "worker_id": threading.get_ident(),
                    "status": "uploaded",
                    "duration_seconds": None,
                    "avg_sec_per_page": None,
                    "concurrency_count": None,
                    "match_query": None,
                    "context_snippet": f"pdf_type={pdf_type}",
                    "error_message": None
                })

            options = [{"label": it["file_name"], "value": it["doc_id"]} for it in items]
            selected = [it["doc_id"] for it in items] if items else []
            summary = f"Uploaded {len(items)} file(s)"

            # For visualization selector, default to first file
            viz_options = [{"label": it["file_name"], "value": it["doc_id"]} for it in items]
            viz_selected = items[0]["doc_id"] if items else None

            return items, dash.no_update, summary, dash.no_update, options, selected, True

        # --------- Análisis de múltiples archivos seleccionados ---------

        elif triggered_id == "run-analysis":
            import time
            ocr_start_time = time.time()

            if not upload_ctx:
                return dash.no_update, dash.no_update, "Upload a PDF first", dash.no_update, dash.no_update, dash.no_update, True

            items = upload_ctx if isinstance(upload_ctx, list) else [upload_ctx]
            selected_ids = selected_doc_id if isinstance(selected_doc_id, list) else [selected_doc_id]
            selected_ids = [sid for sid in selected_ids if sid is not None]
            if not selected_ids:
                return dash.no_update, dash.no_update, "Select file(s) to analyze", dash.no_update, dash.no_update, dash.no_update, True

            from concurrent.futures import ThreadPoolExecutor, as_completed
            results = {}
            errors = {}

            def process_pdf(target):
                try:
                    DEFAULT_OCR_LANG = "eng"
                    DEFAULT_OCR_DPI = 300
                    DEFAULT_OCR_PREPROCESS = ["denoise", "threshold"]
                    pdf_type = target.get("pdf_type", None)
                    if pdf_type == "scanned":
                        from src.extraction.ocr import OCRExtractor
                        denoise = "denoise" in DEFAULT_OCR_PREPROCESS
                        threshold = "threshold" in DEFAULT_OCR_PREPROCESS
                        deskew = "deskew" in DEFAULT_OCR_PREPROCESS
                        ocr = OCRExtractor(lang=DEFAULT_OCR_LANG, dpi=DEFAULT_OCR_DPI, preprocessor=None)
                        ocr.preprocessor = ocr.preprocessor.__class__(denoise=denoise, threshold=threshold, deskew=deskew)
                        pages = ocr.extract(target["file_path"])
                        doc_id = target["doc_id"]
                        result_ctx = {
                            "doc_id": target["doc_id"],
                            "file_path": target["file_path"],
                            "file_name": target["file_name"],
                            "pdf_type": pdf_type,
                            "pages": pages
                        }
                    else:
                        result_ctx = controller.process(
                            target["file_path"], target["file_name"], target["doc_id"], fast_mode=bool(fast_mode)
                        )
                        pages = result_ctx.get("pages", [])
                        doc_id = result_ctx["doc_id"]

                    from src.extraction.field_detection import extract_fields_from_block
                    from src.utils.image import render_page_to_image
                    extracted_fields = []
                    classified_blocks = []
                    overlays_list = []
                    total_blocks = 0
                    classified_count = 0
                    for p in pages:
                        for b in p.get("blocks", []):
                            total_blocks += 1
                            text = b.get("text", "")
                            context = text
                            block_type = b.get("block_type", "other")
                            field_info = extract_fields_from_block(text, context)
                            block_data = {
                                "block_id": b.get("block_id"),
                                "text": text,
                                "block_type": block_type,
                                "confidence": b.get("confidence"),
                                "page": p.get("page_number", 0),
                                "context": context
                            }
                            if field_info:
                                classified_count += 1
                                extracted_fields.append({
                                    "field": field_info["field"],
                                    "value": field_info["value"],
                                    "page": p.get("page_number", 0),
                                    "context": context,
                                    "confidence": b.get("confidence")
                                })
                            classified_blocks.append(block_data)
                    result_ctx["fields"] = extracted_fields
                    result_ctx["classified_blocks"] = classified_blocks
                    confidences = [b.get("confidence") for p in pages for b in p["blocks"] if b.get("confidence") is not None]
                    if pdf_type == "scanned":
                        avg_conf = sum(confidences) / len(confidences) if confidences and pdf_type == "scanned" else None
                    else:
                        avg_conf = (sum(confidences) / len(confidences) * 100) if confidences else None
                    overlays = result_ctx.get("overlays", [])
                    if not overlays:
                        for page_data in pages:
                            try:
                                page_num = page_data.get("page_number")
                                if page_num is None:
                                    continue
                                page_img_path = storage.page_cache_path(doc_id, page_num)
                                render_page_to_image(target["file_path"], page_num, page_img_path)
                                overlay_path = overlay_gen.render_page_overlay(
                                    page_img_path,
                                    page_data.get("blocks", []),
                                    doc_id,
                                    page_num,
                                    page_data.get("width"),
                                    page_data.get("height")
                                )
                                overlays_list.append({"page": page_num, "path": overlay_path})
                            except Exception as e:
                                log_mgr.log({
                                    "timestamp": datetime.now().isoformat(),
                                    "file_id": result_ctx.get("doc_id"),
                                    "filename": result_ctx.get("file_name"),
                                    "step": "OVERLAY",
                                    "page_number": page_num,
                                    "pages_total": result_ctx.get("pages_total"),
                                    "worker_id": threading.get_ident(),
                                    "status": "error",
                                    "duration_seconds": None,
                                    "avg_sec_per_page": None,
                                    "concurrency_count": None,
                                    "match_query": None,
                                    "context_snippet": None,
                                    "error_message": str(e)
                                })
                        result_ctx["overlays"] = overlays_list
                    ocr_end_time = time.time()
                    ocr_duration = ocr_end_time - ocr_start_time
                    viz_duration = result_ctx.get("report", {}).get("visualization_time", 0)
                    result_ctx["report"] = {
                        "visualization_time": viz_duration,
                        "ocr_time": ocr_duration,
                        "total_blocks": total_blocks,
                        "classified_blocks": classified_count,
                        "classification_rate": f"{(classified_count / total_blocks * 100):.1f}%" if total_blocks > 0 else "0%",
                        "extracted_fields": len(extracted_fields),
                        "ocr_confidence": f"{avg_conf:.1f}%" if avg_conf is not None else "N/A"
                    }
                    try:
                        saved_json_path = store.save_document(result_ctx)
                        result_ctx["saved_path"] = saved_json_path
                    except Exception:
                        result_ctx["saved_path"] = None
                    return (target["doc_id"], result_ctx)
                except Exception as e:
                    log_mgr.log({
                        "timestamp": datetime.now().isoformat(),
                        "file_id": target.get("doc_id"),
                        "filename": target.get("file_name"),
                        "step": "OCR_REPORT",
                        "page_number": None,
                        "pages_total": target.get("pages_total"),
                        "worker_id": threading.get_ident(),
                        "status": "error",
                        "duration_seconds": None,
                        "avg_sec_per_page": None,
                        "concurrency_count": None,
                        "match_query": None,
                        "context_snippet": None,
                        "error_message": str(e)
                    })
                    return (target["doc_id"], None)

            item_map = {it["doc_id"]: it for it in items}
            with ThreadPoolExecutor(max_workers=min(4, len(selected_ids))) as executor:
                future_to_docid = {executor.submit(process_pdf, item_map[doc_id]): doc_id for doc_id in selected_ids if doc_id in item_map}
                for future in as_completed(future_to_docid):
                    doc_id, result = future.result()
                    if result is not None:
                        results[doc_id] = result
                    else:
                        errors[doc_id] = True

            viz_doc_id = next(iter(results.keys()), None)
            viz_result = results.get(viz_doc_id) if viz_doc_id else None

            viz_options = [{"label": item_map[doc_id]["file_name"], "value": doc_id} for doc_id in results.keys()]
            summary = (
                f"Processed {viz_result.get('file_name', '?')} — "
                f"pages: {len(viz_result.get('pages', []))} — "
                f"fields: {len(viz_result.get('fields', []))}"
            ) if viz_result else "No PDF processed."

            img_src = dash.no_update
            overlays = viz_result.get("overlays", []) if viz_result else []
            if overlays:
                try:
                    with open(overlays[0]["path"], "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    img_src = f"data:image/png;base64,{b64}"
                except Exception:
                    pass

            # ACTUALIZAR doc-context como dict de doc_id a contexto para que los dropdowns funcionen bien
            doc_context = {doc_id: ctx for doc_id, ctx in results.items()} if results else dash.no_update
            return dash.no_update, doc_context, summary, img_src, viz_options, viz_doc_id, False

        # --------- Sin cambios ---------
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
