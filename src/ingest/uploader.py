"""Docstring for ingest.uploader.

Docstring
"""

import os
from uuid import uuid4
from datetime import datetime, UTC

class IngestManager:
    """Docstring for IngestManager.

    Esta clase no está diseñada para abrir un archivo existente para leerlo. Su propósito es recibir un archivo subido (un stream de bytes) y guardarlo en disco en un directorio específico (data/raw). Es un ingestor: toma lo que le pasas (por ejemplo, desde un formulario web o una API) y lo persist e con un nombre controlado.
    En concreto, el método save_uploaded_file:

    1. Genera un doc_id único (para evitar colisiones).
    2. Crea un nombre de salida con ese doc_id y el filename original: "{doc_id}__{filename}".
    3. Abre un archivo nuevo en esa ruta con open(..., "wb") y escribe los bytes del file_stream.
    4. Devuelve metadatos del archivo guardado (id, ruta, nombre original, timestamp).
    """

    def __init__(self, raw_dir="data/raw"):
        # Creamos el directorio si no existe
        os.makedirs(raw_dir, exist_ok=True)
        self.raw_dir = raw_dir

    def save_uploaded_file(self, file_stream, filename):

        # Generamos un Id unico
        doc_id = str(uuid4())

        # Marca de tiempo actual en formato ISO(saved_at)
        ts = datetime.now(UTC).isoformat()

        # Construye el nombre del archivo
        out_name = f'{doc_id}__{filename}'
        # Une la ruta del directorio con el nombre
        out_path = os.path.join(self.raw_dir, out_name)

        # file_stream: file-like object (bytes)
        try:
            # Intentamos abrir el nuevo archivo
            with open(out_path, "wb") as f:
                # Escribimos los bytes del file_stream
                f.write(file_stream.read())
        except Exception as e:
            return {"error": str(e)}

        # Devuelve metadatos
        return {"doc_id": doc_id, "path": out_path, "filename": filename, "saved_at": ts}