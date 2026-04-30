"""
src/app/handlers/ocr_processing.py
-------------------------------------
Callbacks para OCR: ejecutar OCR, generar overlays y navegar entre páginas.
"""
from __future__ import annotations

import threading
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from src.extraction.ocr import OCRExtractor, OCRPreprocessor
from src.ingest.storage import StorageManager
from src.logs.logger import LogManager
from src.metadata.document_store import DocumentStore
from src.visualization.overlay import OverlayGenerator
from src.utils.doc_enrichment import build_doc_context


def register_callbacks_04(app, controller, embedder=None):

    storage     = StorageManager()
    overlay_gen = OverlayGenerator()
    store       = DocumentStore()
    log_mgr     = LogManager()

    # ── poblar dropdown OCR desde doc-context ─────────────────────────────────
    @app.callback(
        Output("ocr-doc-selector", "options"),
        Output("ocr-doc-selector", "value"),
        Input("doc-context", "data"),
        prevent_initial_call=True,
    )
    def sync_ocr_selector(doc_ctx):
        if not isinstance(doc_ctx, dict) or not doc_ctx:
            return [], None
        opts = [
            {"label": ctx.get("file_name", did), "value": did}
            for did, ctx in doc_ctx.items()
            if isinstance(ctx, dict)
        ]
        return opts, (opts[0]["value"] if opts else None)

    # ── barra de progreso ─────────────────────────────────────────────────────
    @app.callback(
        Output("ocr-progress-bar", "value"),
        Output("ocr-progress-bar", "label"),
        Input("ocr-progress-store", "data"),
    )
    def update_progress_bar(data):
        if not data:
            return 0, "0%"
        val   = data.get("progress", 0)
        total = data.get("total_pages", 1)
        page  = data.get("page", 1)
        label = f"Página {page}/{total} ({val}%)" if total > 1 else f"{val}%"
        return val, label

    # ── ejecutar OCR ──────────────────────────────────────────────────────────
    @app.callback(
        [
            Output("ocr-output",        "children"),
            Output("ocr-messages",      "children"),
            Output("doc-context",       "data",     allow_duplicate=True),
            Output("ocr-progress-store","data"),
        ],
        Input("run-ocr", "n_clicks"),
        State("doc-context",       "data"),
        State("ocr-doc-selector",  "value"),
        State("ocr-language",      "value"),
        State("ocr-dpi",           "value"),
        State("ocr-preprocess",    "value"),
        State("ocr-show-confidence","value"),
        prevent_initial_call=True,
    )
    def run_ocr(n_clicks, doc_ctx, selected_id, lang, dpi, preprocess, show_conf):
        if not doc_ctx or not selected_id:
            raise PreventUpdate

        ctx_doc = doc_ctx.get(selected_id) if isinstance(doc_ctx, dict) else None
        if not ctx_doc or "file_path" not in ctx_doc:
            return (
                dbc.Alert("Documento no encontrado.", color="danger"),
                html.Div(),
                dash.no_update,
                dash.no_update,
            )

        # Preprocessor
        pre = preprocess or []
        ocr = OCRExtractor(
            lang=lang or "eng+spa",
            dpi=int(dpi or 300),
            preprocessor=OCRPreprocessor(
                denoise="denoise" in pre,
                threshold="threshold" in pre,
                deskew="deskew" in pre,
            ),
        )

        pages, images = ocr.extract(ctx_doc["file_path"], return_images=True)
        total         = len(images)
        overlays      = []
        confidences   = []

        for idx, (page, proc_img) in enumerate(zip(pages, images), start=1):
            blocks = page.get("blocks", [])
            for b in blocks:
                c = b.get("confidence")
                if c is not None:
                    confidences.append(float(c))

            page_img_path = storage.page_cache_path(selected_id, idx)
            proc_img.save(page_img_path)

            ov_path = overlay_gen.render_page_overlay(
                page_img_path, blocks, selected_id, idx,
                proc_img.width, proc_img.height,
            )
            if ov_path:
                overlays.append({"page": idx, "path": ov_path})

        avg_conf = sum(confidences) / len(confidences) if confidences else None

        # Actualizar doc_ctx con los nuevos datos OCR
        updated = dict(ctx_doc)
        updated.update({
            "pages":                pages,
            "overlays":             overlays,
            "ocr_language":         lang,
            "ocr_dpi":              dpi or 300,
            "ocr_average_confidence": avg_conf,
            "processing_mode":      "ocr",
        })

        # Re-enriquecer doc_ctx con clasificador mejorado
        enriched = build_doc_context(
            doc_id=updated["doc_id"],
            file_name=updated.get("file_name", ""),
            file_path=updated["file_path"],
            pages=pages,
            overlays=overlays,
            processing_mode="ocr",
        )
        updated.update({
            "classified_blocks": enriched.get("classified_blocks", []),
            "fields":            enriched.get("fields", []),
            "full_text":         enriched.get("full_text", ""),
        })

        try:
            updated["saved_path"] = store.save_document(updated)
        except Exception as e:
            log_mgr.log({"step": "OCR_SAVE", "status": "error",
                         "file_id": selected_id, "error_message": str(e)})

        new_doc_ctx = dict(doc_ctx) if isinstance(doc_ctx, dict) else {}
        new_doc_ctx[selected_id] = updated

        # Mensajes informativos
        msgs = []
        msgs.append(html.Div([html.I(className="bi-check-circle text-success me-2"),
                               f"OCR finalizado: {len(pages)} página(s)"],
                              className="mb-2"))
        if show_conf and avg_conf is not None:
            color = "success" if avg_conf >= 70 else ("warning" if avg_conf >= 45 else "danger")
            msgs.append(dbc.Alert(
                f"Confianza promedio OCR: {avg_conf:.1f}%",
                color=color, className="small mb-2",
            ))
        if avg_conf is not None and avg_conf < 45:
            msgs.append(dbc.Alert(
                "⚠️ Calidad OCR baja. Ajusta DPI, idioma o preprocesado.",
                color="warning", className="small",
            ))
        if overlays:
            msgs.append(html.Div([html.I(className="bi-images text-info me-2"),
                                   f"{len(overlays)} overlay(s) generado(s)"],
                                  className="text-muted small"))

        progress_data = {
            "progress":    100,
            "status":      "Finalizado",
            "page":        1,
            "total_pages": total,
            "overlays":    overlays,
        }

        placeholder = html.Div(
            [html.I(className="bi-arrow-left-right me-2 text-muted"),
             "Usa los botones ◀ ▶ para navegar por las páginas."],
            className="text-muted p-3",
        )

        return placeholder, html.Div(msgs), new_doc_ctx, progress_data

    # ── navegación de overlays OCR ────────────────────────────────────────────
    @app.callback(
        Output("ocr-output",              "children",  allow_duplicate=True),
        Output("overlay-page-indicator-ocr","children", allow_duplicate=True),
        Output("ocr-progress-store",      "data",      allow_duplicate=True),
        Input("overlay-prev-ocr", "n_clicks"),
        Input("overlay-next-ocr", "n_clicks"),
        State("ocr-progress-store", "data"),
        prevent_initial_call=True,
    )
    def navigate_ocr(prev, next_, progress):
        if not progress:
            raise PreventUpdate

        overlays = progress.get("overlays", [])
        total    = progress.get("total_pages", max(len(overlays), 1))
        page     = progress.get("page", 1)

        tid = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if tid == "overlay-prev-ocr":
            page = max(1, page - 1)
        elif tid == "overlay-next-ocr":
            page = min(total, page + 1)

        ov      = next((o for o in overlays if o.get("page") == page), None)
        img_src = ""
        if ov and ov.get("path"):
            from urllib.parse import quote
            abs_p = os.path.abspath(ov["path"])
            if abs_p.startswith(os.path.abspath("data/cache")):
                rel = os.path.relpath(abs_p, os.path.abspath("data/cache")).replace(os.sep, "/")
                img_src = f"/overlays/{quote(rel)}"

        content = (
            html.Img(src=img_src, style={"width": "100%", "height": "auto",
                                          "border": "2px solid #555",
                                          "borderRadius": "8px"})
            if img_src
            else html.Div("No overlay disponible.", className="text-muted p-4")
        )

        updated = dict(progress); updated["page"] = page
        return content, f"Página {page}/{total}", updated


import os
