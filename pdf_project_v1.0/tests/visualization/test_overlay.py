import os
import tempfile
from PIL import Image

from src.visualization.overlay import OverlayGenerator


def _create_dummy_page_image(path, size=(800, 1000)):
    """Crea una imagen blanca simulando una página PDF."""
    img = Image.new("RGB", size, color="white")
    img.save(path)


def test_overlay_file_created_and_non_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1️⃣ Imagen base de la página
        page_img_path = os.path.join(tmpdir, "page_1.png")
        _create_dummy_page_image(page_img_path)

        # 2️⃣ Bloques sintéticos
        blocks = [
            {
                "block_id": 1,
                "bbox": [50, 50, 400, 120],
                "type": "title"
            },
            {
                "block_id": 2,
                "bbox": [50, 150, 750, 300],
                "type": "paragraph"
            },
            {
                "block_id": 3,
                "bbox": [50, 350, 600, 550],
                "type": "table"
            },
        ]

        # 3️⃣ Generar overlay
        generator = OverlayGenerator(cache_dir=tmpdir)
        out_path = generator.render_page_overlay(
            page_image_path=page_img_path,
            blocks=blocks,
            doc_id="test_doc",
            page_num=1,
            show_labels=True
        )

        # 4️⃣ Asserts clave
        assert os.path.exists(out_path), "El archivo overlay no fue creado"
        assert os.path.getsize(out_path) > 0, "El archivo overlay está vacío"