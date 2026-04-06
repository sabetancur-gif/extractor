
import os
import pytest

# Ajusta el import a tu paquete real
from src.ingest.storage import StorageManager


def test_create_doc_folder_creates_directory(tmp_path):
    """
    - Instancia StorageManager con outputs/cache/raw dentro de tmp_path.
    - Llama create_doc_folder(doc_id).
    - Verifica que la ruta devuelta existe y es un directorio.
    """
    outputs_dir = tmp_path / "outputs"
    cache_dir = tmp_path / "cache"
    raw_dir = tmp_path / "raw"

    sm = StorageManager(
        outputs_dir=str(outputs_dir),
        cache_dir=str(cache_dir),
        raw_dir=str(raw_dir),
    )

    doc_id = "doc_123"
    folder = sm.create_doc_folder(doc_id)

    assert isinstance(folder, str), "create_doc_folder debe devolver un string (ruta)"
    assert os.path.exists(folder), "La carpeta del documento debe existir"
    assert os.path.isdir(folder), "La ruta devuelta debe ser un directorio"
    # Además, debe estar dentro de outputs_dir
    assert folder.startswith(str(outputs_dir)), "La carpeta debe crearse dentro de outputs_dir"


def test_page_cache_path_returns_existing_parent_dir(tmp_path):
    """
    - Instancia StorageManager con rutas en tmp_path.
    - Llama page_cache_path(doc_id, page_num).
    - Verifica que el directorio contenedor existe.
    - (Opcional) Crea el archivo en la ruta para comprobar que es utilizable.
    """
    outputs_dir = tmp_path / "outputs"
    cache_dir = tmp_path / "cache"
    raw_dir = tmp_path / "raw"

    sm = StorageManager(
        outputs_dir=str(outputs_dir),
        cache_dir=str(cache_dir),
        raw_dir=str(raw_dir),
    )

    doc_id = "doc_abc"
    page_num = 2
    path = sm.page_cache_path(doc_id, page_num, ext="png")

    # La función crea el directorio .../cache/<doc_id>/pages/
    parent_dir = os.path.dirname(path)
    assert isinstance(path, str), "page_cache_path debe devolver un string (ruta de archivo)"
    assert os.path.exists(parent_dir), "El directorio contenedor de la página debe existir"
    assert os.path.isdir(parent_dir), "El contenedor debe ser un directorio"

    # El archivo en sí NO lo crea la función; comprobamos que la ruta es utilizable
    assert not os.path.exists(path), "El archivo de la página no debe existir aún"
    # Creamos el archivo para confirmar que la ruta es válida
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")  # encabezado PNG mínimo

    assert os.path.exists(path), "La ruta devuelta debe ser válida para crear el archivo"
