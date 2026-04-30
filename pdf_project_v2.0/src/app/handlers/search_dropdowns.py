
"""
src/app/handlers/search_dropdowns.py
------------------------------------
Callbacks para actualizar el dropdown de campos/tipos de bloque en búsqueda avanzada.
"""

# THIRDPARTY
from dash import Input, Output


def register_callbacks_10(app, controller, embedder=None):
    """
    Registra callback para actualizar el dropdown de campos/tipos de bloque en búsqueda avanzada.
    Relacionado con IDs: analysis-search-field, doc-context.
    """

    @app.callback(
        Output("analysis-search-field", "options"),
        Input("doc-context", "data"),
        prevent_initial_call=True,
    )
    def update_field_dropdown(doc_ctx):
        if not doc_ctx or not isinstance(doc_ctx, dict):
            return []
        docs = []

        if isinstance(doc_ctx, dict) and "pages" in doc_ctx:
            docs = [doc_ctx]
        elif isinstance(doc_ctx, dict):
            docs = [v for v in doc_ctx.values() if isinstance(v, dict)]
        elif isinstance(doc_ctx, list):
            docs = [d for d in doc_ctx if isinstance(d, dict)]

        if not docs:
            return []

        all_fields = []
        all_block_types = []

        for d in docs:
            if isinstance(d.get("fields"), list):
                all_fields.extend(d["fields"])

            if isinstance(d.get("classified_blocks"), list):
                all_block_types.extend(
                    [cb.get("block_type") for cb in d["classified_blocks"] if isinstance(cb, dict)]
                )

            if isinstance(d.get("pages"), list):
                for p in d["pages"]:
                    if isinstance(p, dict) and isinstance(p.get("blocks"), list):
                        all_block_types.extend(
                            [b.get("block_type") for b in p["blocks"] if isinstance(b, dict)]
                        )

        unique_fields = sorted({f.get("field") for f in all_fields if  isinstance(f, dict) and f.get("field")})
        unique_block_types = sorted({bt for bt in all_block_types if bt})

        options = [{"label": "Todos los campos", "value": ""}]
        options += [{"label": f"Campo: {f}", "value": f"field:{f}"} for f in unique_fields]
        options += [{"label": f"Tipo bloque: {bt}", "value": f"block:{bt}"} for bt in unique_block_types]

        # Añadir opción para buscar en todo el documento por defecto
        return options
