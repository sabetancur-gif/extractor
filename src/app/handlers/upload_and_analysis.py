"""
src/app/handlers/upload_and_analysis.py
----------------------------------------
Callbacks para upload de PDF y análisis principal (procesamiento, resumen, preview).
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
from src.utils.doc_enrichement import build_doc_context


def register_callbacks_02(app, controller, embedder=None):
    ingest = IngestManager()
    storage = StorageManager()
    log_mgr = LogManager()
    detector = PDFTypeDetector(log_mgr=log_mgr)
    overlay_gen = OverlayGenerator()
    store = DocumentStore()

    def _as_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _build_options(items):
        options = []
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            if not doc_id:
                continue
            label = item.get("file_name") or str(doc_id)
            options.append({"label": label, "value": doc_id})
        return options

    def _unique_by_doc_id(existing_items, new_items):
        merged = []
        seen = set()

        for item in _as_list(existing_items) + _as_list(new_items):
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            if not doc_id or doc_id in seen:
                continue
            seen.add(doc_id)
            merged.append(item)

        return merged

    def _first_preview_src(doc_ctx):
        if not isinstance(doc_ctx, dict) or not doc_ctx:
            return dash.no_update

        first_ctx = next(iter(doc_ctx.values()), None)
        if not isinstance(first_ctx, dict):
            return dash.no_update

        overlays = first_ctx.get("overlays") or []
        if not overlays:
            return dash.no_update

        first_overlay = overlays[0]
        overlay_path = first_overlay.get("path")
        if not overlay_path:
            return dash.no_update

        try:
            with open(overlay_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{b64}"
        except Exception:
            return dash.no_update

    @app.callback(
        [Output("analysis-target", "options"),
         Output("analysis-target", "value")],
        Input("upload-store", "data"),
        prevent_initial_call=True,
    )
    def update_analysis_target(upload_ctx):
        options = _build_options(_as_list(upload_ctx))
        value = [opt["value"] for opt in options] if options else None
        return options, value

    @app.callback(
        [Output("visualization-pdf-selector", "options"),
         Output("visualization-pdf-selector", "value")],
        Input("upload-store", "data"),
        prevent_initial_call=True,
    )
    def update_visualization_selector(upload_ctx):
        options = _build_options(_as_list(upload_ctx))
        value = options[0]["value"] if options else None
        return options, value

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
        ],
        prevent_initial_call=True,
    )
    def handle_upload_and_analysis(contents, n_clicks, filenames, upload_ctx, selected_doc_id, fast_mode):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        # =====================================================
        # UPLOAD
        # =====================================================
        if triggered_id == "upload-pdf":
            contents_list = _as_list(contents)
            filenames_list = _as_list(filenames)

            new_items = []
            for c, fn in zip(contents_list, filenames_list):
                if not c or not fn:
                    continue

                try:
                    _, encoded = c.split(",", 1)
                    file_bytes = io.BytesIO(base64.b64decode(encoded))

                    saved = ingest.save_uploaded_file(file_bytes, fn)
                    pdf_type = detector.detect(saved["path"])

                    new_items.append({
                        "doc_id": saved["doc_id"],
                        "file_name": fn,
                        "file_path": saved["path"],
                        "pdf_type": pdf_type,
                        "status": "uploaded",
                    })
                except Exception as e:
                    log_mgr.log({
                        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        "file_id": None,
                        "filename": fn,
                        "step": "UPLOAD",
                        "status": "error",
                        "error_message": str(e),
                    })

            all_items = _unique_by_doc_id(upload_ctx, new_items)
            summary = f"Uploaded {len(new_items)} file(s)" if new_items else "No files uploaded"

            return all_items, dash.no_update, summary, dash.no_update, True

        # =====================================================
        # ANALYSIS
        # =====================================================
        if triggered_id == "run-analysis":
            items = _as_list(upload_ctx)
            item_map = {
                i["doc_id"]: i
                for i in items
                if isinstance(i, dict) and i.get("doc_id") and i.get("file_path")
            }

            selected_ids = [sid for sid in _as_list(selected_doc_id) if sid]
            if not item_map:
                return dash.no_update, dash.no_update, "Upload a PDF first", dash.no_update, True
            if not selected_ids:
                return dash.no_update, dash.no_update, "Select file(s) to analyze", dash.no_update, True

            from src.extraction.field_detection import extract_fields_from_block
            from src.utils.image import render_page_to_image

            results = {}

            def process_pdf(target):
                try:
                    doc_id = target["doc_id"]
                    file_path = target["file_path"]
                    file_name = target["file_name"]
                    pdf_type = target.get("pdf_type")

                    if pdf_type == "scanned":
                        from src.extraction.ocr import OCRExtractor
                        ocr = OCRExtractor(lang="eng", dpi=300, preprocessor=None)
                        pages = ocr.extract(file_path)
                        if not isinstance(pages, list):
                            pages = []
                        processing_mode = "ocr"
                        result_overlays = []
                    else:
                        result = controller.process(file_path, file_name, doc_id, fast_mode=bool(fast_mode))
                        if not isinstance(result, dict):
                            result = {}
                        pages = result.get("pages", [])
                        if not isinstance(pages, list):
                            pages = []
                        result_overlays = result.get("overlays") or []
                        if not isinstance(result_overlays, list):
                            result_overlays = []
                        processing_mode = "native"

                    extracted_fields = []
                    classified_blocks = []

                    for p in pages:
                        if not isinstance(p, dict):
                            continue

                        page_number = p.get("page_number")
                        blocks = p.get("blocks", [])
                        if not isinstance(blocks, list):
                            blocks = []

                        for b in blocks:
                            if not isinstance(b, dict):
                                continue

                            text = b.get("text", "")
                            field_info = extract_fields_from_block(text, text)

                            classified_blocks.append({
                                **b,
                                "page": page_number,
                            })

                            if field_info:
                                extracted_fields.append({
                                    "field": field_info["field"],
                                    "value": field_info["value"],
                                    "page": page_number,
                                    "page_number": page_number,
                                    "confidence": b.get("confidence"),
                                    "bbox": b.get("bbox"),
                                    "block_id": b.get("block_id"),
                                    "text": text,
                                    "semantic_type": field_info["field"],
                                    "source": {
                                        **b,
                                        "detected_field": field_info["field"],
                                        "detected_value": field_info["value"],
                                    },
                                })

                    overlays = []

                    if result_overlays:
                        overlays = result_overlays
                    else:
                        for p in pages:
                            if not isinstance(p, dict):
                                continue

                            pn = p.get("page_number")
                            if pn is None:
                                continue

                            blocks = p.get("blocks") or []
                            if not isinstance(blocks, list):
                                blocks = []

                            try:
                                img_path = storage.page_cache_path(doc_id, pn)
                                render_page_to_image(file_path, pn, img_path)

                                overlay_path = overlay_gen.render_page_overlay(
                                    img_path,
                                    blocks,
                                    doc_id,
                                    pn,
                                    p.get("width"),
                                    p.get("height"),
                                )

                                if overlay_path:
                                    overlays.append({"page": pn, "path": overlay_path})

                            except Exception as page_err:
                                log_mgr.log({
                                    "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                                    "file_id": doc_id,
                                    "filename": file_name,
                                    "step": "OVERLAY",
                                    "status": "error",
                                    "error_message": str(page_err),
                                })
                                continue

                    doc_ctx = build_doc_context(
                        doc_id=doc_id,
                        file_name=file_name,
                        file_path=file_path,
                        pages=pages,
                        overlays=overlays,
                        pdf_type=pdf_type,
                        processing_mode=processing_mode,
                        extra_meta={
                            "source": "upload",
                            "uploaded_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        },
                    )

                    doc_ctx["fields"] = extracted_fields
                    doc_ctx["classified_blocks"] = classified_blocks
                    doc_ctx["report"] = {
                        "pages": len(pages),
                        "blocks": len(classified_blocks),
                        "fields": len(extracted_fields),
                    }

                    try:
                        doc_ctx["saved_path"] = store.save_document(doc_ctx)
                    except Exception:
                        doc_ctx["saved_path"] = None

                    return doc_id, doc_ctx

                except Exception as e:
                    import traceback
                    log_mgr.log({
                        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        "file_id": target.get("doc_id"),
                        "filename": target.get("file_name"),
                        "step": "PROCESS_PDF",
                        "status": "error",
                        "error_message": f"{e}\n{traceback.format_exc()}",
                    })
                    return target.get("doc_id"), None

            selected_ids = [sid for sid in selected_ids if sid in item_map]

            if not selected_ids:
                return dash.no_update, dash.no_update, "No valid PDF selected", dash.no_update, True

            with ThreadPoolExecutor(max_workers=min(4, len(selected_ids))) as executor:
                futures = [
                    executor.submit(process_pdf, item_map[doc_id])
                    for doc_id in selected_ids
                ]
                for future in as_completed(futures):
                    doc_id, result = future.result()
                    if doc_id and result:
                        results[doc_id] = result

            if not results:
                return dash.no_update, dash.no_update, "No PDF processed.", dash.no_update, True

            summary = f"Processed {len(results)} document(s)"
            preview_src = _first_preview_src(results)

            return dash.no_update, results, summary, preview_src, False

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
