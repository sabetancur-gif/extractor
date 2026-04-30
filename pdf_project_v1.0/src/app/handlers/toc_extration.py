
"""
src/app/handlers/toc_extration.py
-------------------------------
Callbacks para extracción de tabla de contenidos (TOC).
"""

# STDLIB
import json
import os

# THIRDPARTY
import dash
from dash import Input, Output, State, html


def register_callbacks_07(app, controller, embedder=None):
    """
    Registra callback para extraer la tabla de contenidos del documento.
    Relacionado con IDs: toc-output, extract-toc, doc-context.
    """
    @app.callback(
        Output("toc-output", "children"),
        Input("extract-toc", "n_clicks"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def extract_toc(n_clicks, doc_ctx):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        # Cargar siempre desde JSON si existe
        json_path = doc_ctx.get("saved_path")
        doc = doc_ctx
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception:
                doc = doc_ctx

        pages = doc.get("pages", [])
        toc = []
        # Recopilar títulos y jerarquía por font_size (mayor tamaño = nivel superior)
        for p in pages:
            for b in p.get("blocks", []):
                if b.get("type") == "title":
                    toc.append({
                        "title": b.get("text", ""),
                        "page": p["page_number"],
                        "font_size": b.get("font_size", 0)
                    })
        if not toc:
            return "No TOC found"
        # Determinar niveles jerárquicos por font_size
        sizes = sorted(set(t["font_size"] for t in toc if t["font_size"]), reverse=True)

        def get_level(font_size):
            for i, sz in enumerate(sizes):
                if font_size >= sz:
                    return i
            return len(sizes)
        # Construir estructura anidada
        tree = []
        stack = [(tree, -1)]
        for t in toc:
            lvl = get_level(t["font_size"])
            node = {"title": t["title"], "page": t["page"], "children": []}
            while stack and stack[-1][1] >= lvl:
                stack.pop()
            stack[-1][0].append(node)
            stack.append((node["children"], lvl))

        # Renderizar como lista anidada
        def render_tree(nodes):
            return html.Ul([
                html.Li([
                    html.Span(f"{n['title']} (p {n['page']})", style={"fontWeight": "bold" if not n["children"] else "normal"}),
                    render_tree(n["children"]) if n["children"] else None
                ]) for n in nodes
            ])
        return html.Div([
            html.H6("Tabla de Contenidos extraída"),
            render_tree(tree)
        ])
