
import os
import pytest
from PIL import Image

# Ajusta estos imports según tu estructura real de paquete
from src.utils.image import render_page_to_image, render_all_pages


def test_render_page_to_image_saves_png_and_returns_path(tmp_path, monkeypatch):
    """
    - Mock convert_from_path para que devuelva una sola imagen PIL.
    - Llama render_page_to_image.
    - Verifica que el archivo se cree, que sea PNG y que el path devuelto exista.
    """
    # Ruta ficticia de entrada y salida
    pdf_path = tmp_path / "dummy.pdf"
    out_path = tmp_path / "out.png"
    # El módulo no usa el contenido del PDF; sólo pasamos el path
    pdf_path.write_bytes(b"%PDF-1.4\n%Fake\n")  # marcador mínimo, aunque no se usa

    # Crear una imagen PIL en memoria que simule la salida de convert_from_path
    fake_img = Image.new("RGB", (100, 100), color="red")

    # Mock de convert_from_path
    def fake_convert_from_path(file_path, dpi=150, first_page=None, last_page=None):
        # Validaciones ligeras para asegurar que pasamos los params
        assert file_path == str(pdf_path)
        assert isinstance(dpi, int) and dpi > 0
        assert first_page == 1
        assert last_page == 1
        return [fake_img]

    # Aplicar el mock
    monkeypatch.setattr("src.utils.image.convert_from_path", fake_convert_from_path)

    # Ejecutar la función
    result_path = render_page_to_image(str(pdf_path), page_num=1, out_path=str(out_path), dpi=150)

    # Asserts
    assert isinstance(result_path, str), "Debe devolver el path (str)"
    assert os.path.exists(result_path), "El archivo PNG debe existir"
    # Comprobar que realmente es un PNG
    with Image.open(result_path) as im:
        assert im.format == "PNG", "El archivo guardado debe ser PNG"
        assert im.size == (100, 100), "Dimensiones deben corresponder a la imagen mockeada"


def test_render_page_to_image_raises_on_empty_images(tmp_path, monkeypatch):
    """
    - Mock convert_from_path para que devuelva lista vacía.
    - Verifica que levanta RuntimeError.
    """
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    def fake_convert_empty(file_path, dpi=150, first_page=None, last_page=None):
        return []

    monkeypatch.setattr("src.utils.image.convert_from_path", fake_convert_empty)

    with pytest.raises(RuntimeError, match="No images returned"):
        render_page_to_image(str(pdf_path), page_num=1, out_path=str(tmp_path / "out.png"), dpi=150)


def test_render_all_pages_creates_folder_and_saves_all(tmp_path, monkeypatch):
    """
    - Mock convert_from_path para que devuelva múltiples imágenes PIL.
    - Llama render_all_pages.
    - Verifica que el folder se crea, que los archivos existen y que devuelve la lista de paths.
    """
    pdf_path = tmp_path / "dummy.pdf"
    out_folder = tmp_path / "pages"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    # Simular 3 páginas/imágenes
    fake_images = [
        Image.new("RGB", (50, 50), color="blue"),
        Image.new("RGB", (60, 60), color="green"),
        Image.new("RGB", (70, 70), color="yellow"),
    ]

    def fake_convert(file_path, dpi=150):
        assert file_path == str(pdf_path)
        assert isinstance(dpi, int) and dpi > 0
        return fake_images

    monkeypatch.setattr("src.utils.image.convert_from_path", fake_convert)

    paths = render_all_pages(str(pdf_path), out_folder=str(out_folder), dpi=200)

    # Asserts principales
    assert isinstance(paths, list), "Debe devolver una lista de rutas"
    assert len(paths) == 3, "Debe devolver tantas rutas como imágenes renderizadas"
    assert os.path.isdir(out_folder), "La carpeta de salida debe existir"

    # Verificar que los archivos existen y son PNG
    for i, p in enumerate(paths, start=1):
        assert os.path.exists(p), f"El archivo de la página {i} debe existir"
        assert os.path.basename(p) == f"page_{i}.png", "Nombre de archivo esperado"
        with Image.open(p) as im:
            assert im.format == "PNG", "Cada archivo debe ser PNG"