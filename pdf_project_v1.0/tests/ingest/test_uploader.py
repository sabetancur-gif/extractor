

# tests/test_ingest_manager.py
import os
from io import BytesIO
from uuid import UUID
from datetime import datetime
import pytest

# Importa el módulo/clase desde tu archivo real
# Si tu clase está en ingest_manager.py:
from src.ingest.uploader import IngestManager


def test_save_uploaded_file_saves_bytes_and_returns_metadata(tmp_path):
    """
    Prueba principal:
    - Crea el directorio temporal como raw_dir
    - Guarda un archivo con contenido
    - Verifica que se escribió y que los metadatos son correctos
    """
    raw_dir = tmp_path / "data" / "raw"
    mgr = IngestManager(raw_dir=str(raw_dir))

    filename = "ejemplo.pdf"
    content = b"contenido de prueba"
    file_stream = BytesIO(content)

    result = mgr.save_uploaded_file(file_stream, filename)

    # Metadatos esperados
    assert "doc_id" in result and isinstance(result["doc_id"], str)
    assert "path" in result and isinstance(result["path"], str)
    assert "filename" in result and result["filename"] == filename
    assert "saved_at" in result and isinstance(result["saved_at"], str)

    # doc_id debería ser un UUID válido
    UUID(result["doc_id"])  # no debería lanzar excepción

    # saved_at debería ser un ISO-8601 válido (con o sin microsegundos)
    dt = datetime.fromisoformat(result["saved_at"])
    assert isinstance(dt, datetime)

    # El archivo debe existir en el sistema
    assert os.path.exists(result["path"])

    # El nombre de salida debe incluir doc_id y filename unidos por '__'
    basename = os.path.basename(result["path"])
    assert basename.endswith(f"__{filename}")
    assert basename.startswith(result["doc_id"])

    # El contenido debe coincidir
    with open(result["path"], "rb") as f:
        saved = f.read()
    assert saved == content


def test_save_uploaded_file_with_empty_content(tmp_path):
    """
    Guardar un archivo vacío (0 bytes) debe crear el archivo sin errores.
    """
    raw_dir = tmp_path / "data" / "raw"
    mgr = IngestManager(raw_dir=str(raw_dir))

    filename = "vacío.bin"
    file_stream = BytesIO(b"")

    result = mgr.save_uploaded_file(file_stream, filename)

    assert os.path.exists(result["path"])
    assert os.path.getsize(result["path"]) == 0


def test_raw_dir_is_created_if_missing(tmp_path):
    """
    Si el directorio no existe, IngestManager debe crearlo.
    """
    raw_dir = tmp_path / "no_existe" / "profundo"
    assert not raw_dir.exists()

    mgr = IngestManager(raw_dir=str(raw_dir))
    assert raw_dir.exists()  # creado por os.makedirs(..., exist_ok=True)

    # Guardar para asegurar que se usa el directorio correcto
    result = mgr.save_uploaded_file(BytesIO(b"hola"), "a.txt")
    assert os.path.dirname(result["path"]) == str(raw_dir)


def test_error_when_file_stream_has_no_read(tmp_path):
    """
    Si el objeto no tiene .read(), el método debería lanzar un AttributeError.
    (nuestra implementación actual captura excepciones, si no fuera así usamos
    with pytest.raises(AttributeError).)
    """
    class NoRead:
        pass

    raw_dir = tmp_path / "data" / "raw"
    mgr = IngestManager(raw_dir=str(raw_dir))

    result = mgr.save_uploaded_file(NoRead(), "a.txt")
    assert isinstance(result, dict)
    assert "error" in result
    assert "read" in result["error"].lower()
