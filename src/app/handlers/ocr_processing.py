"""Callbacks para procesamiento OCR y navegación de overlays OCR."""

# STDLIB

import threading
from datetime import datetime

# THIRDPARTY
import dash
from dash import Input, Output, State, dcc, html

import dash_bootstrap_components as dbc


# FIRSTPARTY
from src.extraction.ocr import OCRExtractor
from src.ingest.storage import StorageManager
from src.metadata.document_store import DocumentStore
from src.visualization.overlay import OverlayGenerator


def register_callbacks_04(app, controller, embedder=None):  # This line is correct and should remain
    """Registra callbacks para procesamiento y navegación de overlays OCR."""
    # Callback para poblar el dropdown de selección de documento en OCR SOLO con los procesados (doc-context)
    # @app.callback(
    #     Output("ocr-doc-selector", "options"),
    #     Output("ocr-doc-selector", "value"),
    #     Input("doc-context", "data"),
    #     prevent_initial_call=True
    # )
    # def update_ocr_doc_selector(doc_ctx):
    #     if not doc_ctx or not isinstance(doc_ctx, dict):
    #         return [], None
    #     options = []
    #     for doc_id, ctx in doc_ctx.items():
    #         if isinstance(ctx, dict):
    #             label = ctx.get("file_name", doc_id)
    #         else:
    #             label = str(doc_id)
    #         options.append({"label": label, "value": doc_id})
    #     value = options[0]["value"] if options else None
    #     return options, value
    
    @app.callback(
        Output("ocr-doc-selector", "options"),
        Output("ocr-doc-selector", "value"),
        Input("doc-context", "data"),
        prevent_initial_call=True
    )
    def update_ocr_doc_selector(doc_ctx):
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

    """Registra callbacks para navegación de overlays en el tab OCR Processing.
    Relacionado con IDs: ocr-output, overlay-page-indicator-ocr, overlay-prev-ocr, overlay-next-ocr, ocr-progress-store.
    """

    # Callback para navegación de overlays en OCR Processing
    
    @app.callback(
        Output("ocr-output", "children", allow_duplicate=True),
        Output("overlay-page-indicator-ocr", "children", allow_duplicate=True),
        Output("ocr-progress-store", "data", allow_duplicate=True),   # <--- NUEVO: persistir page
        Input("overlay-prev-ocr", "n_clicks"),
        Input("overlay-next-ocr", "n_clicks"),
        State("ocr-progress-store", "data"),
        State("ocr-doc-selector", "value"),
        prevent_initial_call=True
    )
    def navigate_ocr_overlays(prev_clicks, next_clicks, progress_data, selected_doc_id):
        overlays = []
        total = 1
        page = 1

        # Usar datos del store, con posibilidad de estructura por documento o simple
        if progress_data and selected_doc_id:
            if isinstance(progress_data.get("overlays"), dict):
                doc_overlays = progress_data["overlays"].get(selected_doc_id, [])
                overlays = doc_overlays
                total = progress_data.get("total_pages", {}).get(selected_doc_id, 1)
                page = progress_data.get("page", {}).get(selected_doc_id, 1)
            else:
                overlays = progress_data.get("overlays", [])
                total = progress_data.get("total_pages", 1)
                page = progress_data.get("page", 1)
        elif progress_data:
            overlays = progress_data.get("overlays", [])
            total = progress_data.get("total_pages", 1)
            page = progress_data.get("page", 1)

        if not page or page == 0:
            page = 1
        if not total or total == 0:
            total = max(1, len(overlays) or 1)

        # Determinar qué botón disparó
        ctx = dash.callback_context
        triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        if triggered == "overlay-prev-ocr":
            page = max(1, page - 1)
        elif triggered == "overlay-next-ocr":
            page = min(total, page + 1)

        # Buscar overlay para la página actual
        overlay = next((o for o in overlays if o.get("page") == page), None)
        img_src = ""
        debug_info = []

        if overlay and overlay.get("path"):
            from urllib.parse import quote
            import os
            OVERLAY_DIR = os.path.abspath("data/cache")
            path = os.path.abspath(overlay["path"])
            base = os.path.abspath(OVERLAY_DIR)
            if path.startswith(base):
                rel = os.path.relpath(path, base).replace(os.sep, "/")
                img_src = f"/overlays/{quote(rel)}"
            else:
                debug_info.append(html.Div(f"Path no está dentro de {base}"))
            if not os.path.exists(path):
                debug_info.append(html.Div(f"Archivo no existe: {path}", style={"color": "red"}))

        # Construir contenido visual (solo overlay)
        if img_src:
            img = html.Img(
                src=img_src,
                style={
                    "width": "100%",
                    "height": "auto",
                    "display": "block",
                    "marginLeft": "auto",
                    "marginRight": "auto",
                    "border": "2px solid #888",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                }
            )
            content = html.Div([img] + debug_info)
        else:
            content = html.Div("No overlay disponible", className="text-muted")

        indicator = f"Página {page}/{total}"

        # === Persistir página en el store para que la navegación avance correctamente ===
        updated_store = dict(progress_data or {})
        # Mantener compatibilidad con estructura simple o por documento
        if isinstance(updated_store.get("page"), dict) and selected_doc_id:
            updated_store.setdefault("page", {})
            updated_store["page"][selected_doc_id] = page
        else:
            updated_store["page"] = page

        # Asegurar total_pages coherente si no existiera
        if isinstance(updated_store.get("total_pages"), dict) and selected_doc_id:
            updated_store.setdefault("total_pages", {})
            if not updated_store["total_pages"].get(selected_doc_id):
                updated_store["total_pages"][selected_doc_id] = total
        else:
            updated_store["total_pages"] = updated_store.get("total_pages") or total

        # Reinyectar overlays (sin cambios)
        if overlays:
            updated_store["overlays"] = updated_store.get("overlays", overlays)

        return content, indicator, updated_store

    # @app.callback(
    #     Output("ocr-output", "children", allow_duplicate=True),
    #     Output("overlay-page-indicator-ocr", "children", allow_duplicate=True),
    #     Input("overlay-prev-ocr", "n_clicks"),
    #     Input("overlay-next-ocr", "n_clicks"),
    #     State("ocr-progress-store", "data"),
    #     State("ocr-doc-selector", "value"),
    #     prevent_initial_call=True
    # )
    # def navigate_ocr_overlays(prev_clicks, next_clicks, progress_data, selected_doc_id):
    #     overlays = []
    #     total = 1
    #     page = 1

    #     # Filtrar overlays y total_pages por documento seleccionado si la estructura lo permite
    #     if progress_data and selected_doc_id:

    #         if isinstance(progress_data.get("overlays"), dict):
    #             doc_overlays = progress_data["overlays"].get(selected_doc_id, [])
    #             overlays = doc_overlays
    #             total = progress_data.get("total_pages", {}).get(selected_doc_id, 1)
    #             page = progress_data.get("page", {}).get(selected_doc_id, 1)
    #         else:
    #             overlays = progress_data.get("overlays", [])
    #             total = progress_data.get("total_pages", 1)
    #             page = progress_data.get("page", 1)

    #     elif progress_data:
    #         overlays = progress_data.get("overlays", [])
    #         total = progress_data.get("total_pages", 1)
    #         page = progress_data.get("page", 1)
    #     if not page or page == 0:
    #         page = 1

    #     ctx = dash.callback_context
    #     triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    #     if triggered == "overlay-prev-ocr":
    #         page = max(1, page - 1)
    #     elif triggered == "overlay-next-ocr":
    #         page = min(total, page + 1)

    #     # Mensajes de estado
    #     status_msgs = []
    #     if overlays:
    #         status_msgs.append(html.Div(f"✅ {len(overlays)} overlay(s) generado(s)", className="text-success mt-2"))
    #     else:
    #         status_msgs.append(html.Div("No overlays disponibles", className="text-danger mt-2"))

    #     # Mostrar solo el overlay de la página actual
    #     overlay = next((o for o in overlays if o.get("page") == page), None)
    #     img_src = ""
    #     debug_info = []
    #     if overlay:
    #         debug_info.append(html.Div(f"Overlay encontrado para page={page}: {overlay}"))
    #     else:
    #         debug_info.append(html.Div(f"No overlay para page={page}"))
    #     if overlay and overlay.get("path"):
    #         from urllib.parse import quote
    #         import os
    #         OVERLAY_DIR = os.path.abspath("data/cache")
    #         path = os.path.abspath(overlay["path"])
    #         base = os.path.abspath(OVERLAY_DIR)
    #         debug_info.append(html.Div(f"Path generado: {path}"))
    #         if path.startswith(base):
    #             rel = os.path.relpath(path, base).replace(os.sep, "/")
    #             img_src = f"/overlays/{quote(rel)}"
    #         else:
    #             debug_info.append(html.Div(f"Path no está dentro de {base}"))
    #         if not os.path.exists(path):
    #             debug_info.append(html.Div(f"Archivo no existe: {path}", style={"color": "red"}))
    #     img = html.Img(
    #         src=img_src,
    #         style={
    #             "width": "100%",
    #             "maxWidth": "600px",
    #             "display": "block",
    #             "marginLeft": "auto",
    #             "marginRight": "auto",
    #             "border": "2px solid #888",
    #             "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
    #         }
    #     ) if img_src else html.Div("No overlay disponible")

    #     # Layout tipo Visualization: dbc.Row, dbc.Col, dbc.Card
    #     content = dbc.Row([
    #         dbc.Col([
    #             dbc.Card([
    #                 dbc.CardHeader(html.H5("Información OCR", className="fw-bold")),
    #                 dbc.CardBody(status_msgs + debug_info)
    #             ], className="shadow-lg border-0 mb-3")
    #         ], md=4, xs=12),
    #         dbc.Col([
    #             dbc.Card([
    #                 dbc.CardHeader(html.H5(f"Overlay Página {page}/{total}", className="fw-bold")),
    #                 dbc.CardBody([
    #                     img
    #                 ], style={"textAlign": "center"})
    #             ], className="shadow-lg border-0 mb-3")
    #         ], md=8, xs=12)
    #     ], className="g-3")
    #     indicator = f"Página {page}/{total}"
    #     return content, indicator

    # Callback para actualizar la barra de progreso visual en la UI
    @app.callback(
        Output("ocr-progress-bar", "value"),
        Output("ocr-progress-bar", "label"),
        Input("ocr-progress-store", "data")
    )
    def update_ocr_progress_bar(progress_data):
        value = progress_data.get("progress", 0) if progress_data else 0
        total = progress_data.get("total_pages", 1) if progress_data else 1
        page = progress_data.get("page", 1) if progress_data else 1
        label = f"Página {page}/{total} ({value}%)" if total > 1 else f"{value}%"
        return value, label

    # storage = StorageManager()
    # overlay_gen = OverlayGenerator()
    # store = DocumentStore()
    # from src.logs.logger import LogManager
    # log_mgr = LogManager()

    # @app.callback(
    #     [
    #         Output("ocr-output", "children"),
    #         Output("doc-context", "data", allow_duplicate=True),
    #         Output("ocr-progress-store", "data"),
    #     ],
    #     Input("run-ocr", "n_clicks"),
    #     State("doc-context", "data"),
    #     State("ocr-doc-selector", "value"),
    #     State("ocr-language", "value"),
    #     State("ocr-dpi", "value"),
    #     State("ocr-preprocess", "value"),
    #     State("ocr-show-confidence", "value"),
    #     prevent_initial_call=True,
    # )
    # def run_ocr(n_clicks, doc_ctx, selected_doc_id, lang, dpi, preprocess, show_conf):
    #     if not doc_ctx or not selected_doc_id:
    #         raise dash.exceptions.PreventUpdate

    #     # Buscar el contexto del documento seleccionado
    #     ctx = None
    #     if isinstance(doc_ctx, dict):
    #         ctx = doc_ctx.get(selected_doc_id)
    #     if not ctx or "file_path" not in ctx:
    #         return dash.no_update, dash.no_update, dash.no_update

    #     # Preprocesado
    #     print("1")
    #     denoise = "denoise" in (preprocess or [])
    #     threshold = "threshold" in (preprocess or [])
    #     deskew = "deskew" in (preprocess or [])
    #     ocr = OCRExtractor(lang=lang, dpi=dpi or 300, preprocessor=None)
    #     # Sobrescribe preprocessor
    #     ocr.preprocessor = ocr.preprocessor.__class__(denoise=denoise, threshold=threshold, deskew=deskew)

    #     # Progreso visual en la UI
    #     # imports innecesarios removidos
    #     print(f"paths: {ctx['file_path']}")
    #     pages, images = ocr.extract(ctx["file_path"], return_images=True) if hasattr(ocr, "extract") else ([], [])
    #     total_pages = len(images)
    #     overlays_list = []
    #     confidences = []
    #     print("2")
    #     for idx, (page, proc) in enumerate(zip(pages, images), start=1):
    #         blocks = page["blocks"]
    #         for block in blocks:
    #             if block.get("confidence") is not None:
    #                 confidences.append(block["confidence"])
    #         # Generar overlay para la página
    #         page_img_path = storage.page_cache_path(ctx["doc_id"], idx)
    #         proc.save(page_img_path)
    #         overlay_path = overlay_gen.render_page_overlay(
    #             page_img_path,
    #             blocks,
    #             ctx["doc_id"],
    #             idx,
    #             proc.width,
    #             proc.height
    #         )
    #         overlays_list.append({"page": idx, "path": overlay_path})
    #     avg_conf = sum(confidences) / len(confidences) if confidences else None

    #     # Finalizar y guardar contexto
    #     updated_ctx = dict(ctx)
    #     updated_ctx["pages"] = pages
    #     updated_ctx["ocr_language"] = lang
    #     updated_ctx["ocr_dpi"] = dpi or 300
    #     updated_ctx["ocr_average_confidence"] = avg_conf
    #     updated_ctx["overlays"] = overlays_list
    #     # Guardar contexto persistentemente
    #     try:
    #         saved_json_path = store.save_document(updated_ctx)
    #         updated_ctx["saved_path"] = saved_json_path
    #     except Exception as e:
    #         log_mgr.log({
    #             "timestamp": datetime.now().isoformat(),
    #             "file_id": updated_ctx.get("doc_id"),
    #             "filename": updated_ctx.get("file_name"),
    #             "step": "SAVE",
    #             "page_number": None,
    #             "pages_total": updated_ctx.get("pages_total"),
    #             "worker_id": threading.get_ident(),
    #             "status": "error",
    #             "duration_seconds": None,
    #             "avg_sec_per_page": None,
    #             "concurrency_count": None,
    #             "match_query": None,
    #             "context_snippet": None,
    #             "error_message": str(e)
    #         })
    #     # Actualizar el contexto del documento seleccionado en doc_ctx
    #     new_doc_ctx = dict(doc_ctx) if isinstance(doc_ctx, dict) else {}
    #     new_doc_ctx[selected_doc_id] = updated_ctx
    #     # Mostrar la primera página
    #     children = [
    #         dcc.Markdown(f"**OCR pages:** {len(pages)}"),
    #     ]
    #     if show_conf:
    #         children.append(dcc.Markdown(f"**Confianza promedio OCR:** {avg_conf:.1f}" if avg_conf is not None else "Confianza no disponible"))
    #     if avg_conf is not None and avg_conf < 60:
    #         children.append(html.Div("⚠️ La calidad del OCR es baja. Prueba ajustar DPI, idioma o preprocesado.", className="text-danger mt-2"))
    #     if updated_ctx.get("saved_path"):
    #         children.append(html.Div(f"✅ Datos guardados en: {updated_ctx['saved_path']}", className="text-success mt-2"))
    #     if overlays_list:
    #         children.append(html.Div(f"✅ {len(overlays_list)} overlay(s) generado(s)", className="text-success mt-2"))
    #     # Progreso final al 100%, page inicia en 1
    #     progress_data = {"progress": 100, "status": "Finalizado", "page": 1, "total_pages": total_pages, "overlays": overlays_list}
    #     # Do NOT show the overlay image here; let navigation callback handle it
    #     return html.Div(children), new_doc_ctx, progress_data
    storage = StorageManager()
    overlay_gen = OverlayGenerator()
    store = DocumentStore()
    from src.logs.logger import LogManager
    log_mgr = LogManager()

    @app.callback(
        [
            Output("ocr-output", "children"),
            Output("ocr-messages", "children"),
            Output("doc-context", "data", allow_duplicate=True),
            Output("ocr-progress-store", "data"),
        ],
        Input("run-ocr", "n_clicks"),
        State("doc-context", "data"),
        State("ocr-doc-selector", "value"),
        State("ocr-language", "value"),
        State("ocr-dpi", "value"),
        State("ocr-preprocess", "value"),
        State("ocr-show-confidence", "value"),
        prevent_initial_call=True,
    )
    def run_ocr(n_clicks, doc_ctx, selected_doc_id, lang, dpi, preprocess, show_conf):
        if not doc_ctx or not selected_doc_id:
            raise dash.exceptions.PreventUpdate

        # Buscar el contexto del documento seleccionado
        ctx = None
        if isinstance(doc_ctx, dict):
            ctx = doc_ctx.get(selected_doc_id)
        if not ctx or "file_path" not in ctx:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Preprocesado
        denoise = "denoise" in (preprocess or [])
        threshold = "threshold" in (preprocess or [])
        deskew = "deskew" in (preprocess or [])
        ocr = OCRExtractor(lang=lang, dpi=dpi or 300, preprocessor=None)
        # Sobrescribe preprocessor
        ocr.preprocessor = ocr.preprocessor.__class__(denoise=denoise, threshold=threshold, deskew=deskew)

        # OCR
        pages, images = ocr.extract(ctx["file_path"], return_images=True) if hasattr(ocr, "extract") else ([], [])
        total_pages = len(images)
        overlays_list = []
        confidences = []

        for idx, (page, proc) in enumerate(zip(pages, images), start=1):
            blocks = page["blocks"]
            for block in blocks:
                if block.get("confidence") is not None:
                    confidences.append(block["confidence"])
            # Generar overlay para la página
            page_img_path = storage.page_cache_path(ctx["doc_id"], idx)
            proc.save(page_img_path)
            overlay_path = overlay_gen.render_page_overlay(
                page_img_path,
                blocks,
                ctx["doc_id"],
                idx,
                proc.width,
                proc.height
            )
            overlays_list.append({"page": idx, "path": overlay_path})

        avg_conf = sum(confidences) / len(confidences) if confidences else None

        # Finalizar y guardar contexto
        updated_ctx = dict(ctx)
        updated_ctx["pages"] = pages
        updated_ctx["ocr_language"] = lang
        updated_ctx["ocr_dpi"] = dpi or 300
        updated_ctx["ocr_average_confidence"] = avg_conf
        updated_ctx["overlays"] = overlays_list

        try:
            saved_json_path = store.save_document(updated_ctx)
            updated_ctx["saved_path"] = saved_json_path
        except Exception as e:
            log_mgr.log({
                "timestamp": datetime.now().isoformat(),
                "file_id": updated_ctx.get("doc_id"),
                "filename": updated_ctx.get("file_name"),
                "step": "SAVE",
                "page_number": None,
                "pages_total": updated_ctx.get("pages_total"),
                "worker_id": threading.get_ident(),
                "status": "error",
                "duration_seconds": None,
                "avg_sec_per_page": None,
                "concurrency_count": None,
                "match_query": None,
                "context_snippet": None,
                "error_message": str(e)
            })

        # Actualizar el contexto del documento seleccionado en doc_ctx
        new_doc_ctx = dict(doc_ctx) if isinstance(doc_ctx, dict) else {}
        new_doc_ctx[selected_doc_id] = updated_ctx

        # Mensajes (tarjeta derecha)
        messages_children = [
            dcc.Markdown(f"**OCR pages:** {len(pages)}"),
        ]
        if show_conf:
            messages_children.append(
                dcc.Markdown(f"**Confianza promedio OCR:** {avg_conf:.1f}" if avg_conf is not None else "Confianza no disponible")
            )
        if avg_conf is not None and avg_conf < 60:
            messages_children.append(
                html.Div("⚠️ La calidad del OCR es baja. Prueba ajustar DPI, idioma o preprocesado.", className="text-danger mt-2")
            )
        if updated_ctx.get("saved_path"):
            messages_children.append(html.Div([html.Strong("✅ Datos guardados en: "), updated_ctx['saved_path']], className="text-success mt-2"))
        if overlays_list:
            messages_children.append(html.Div([html.Strong(f"✅ {len(overlays_list)} overlay(s) generado(s)")], className="text-success mt-2"))

        # Progreso final al 100%, page inicia en 1
        progress_data = {
            "progress": 100,
            "status": "Finalizado",
            "page": 1,
            "total_pages": total_pages,
            "overlays": overlays_list
        }

        # IZQUIERDA: no mostrar imagen aquí; navegación se encarga
        left_placeholder = html.Div(
            "Procesamiento finalizado. Usa los botones ◀ ▶ para navegar por las páginas.",
            className="text-muted"
        )

        return left_placeholder, messages_children, new_doc_ctx, progress_data