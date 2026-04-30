# Project Structure

pdf_dash_project
├── config
│   └── config.example.yaml
├── docs
├── src
│   ├── app
│   │   ├── assets
│   │   │   └── style.css
│   │   ├── handlers
│   │   │   ├── clustering.py
│   │   │   ├── document_search.py
│   │   │   ├── download_visualization.py
│   │   │   ├── export_converters.py
│   │   │   ├── ocr_navigation.py
│   │   │   ├── ocr_processing.py
│   │   │   ├── overlays.py
│   │   │   ├── search_dropdowns.py
│   │   │   ├── sidebar_toggle.py
│   │   │   ├── toc_extration.py
│   │   │   ├── translation.py
│   │   │   ├── upload_and_analysis.py
│   │   │   ├── visualization_download.py
│   │   │   └── visualization_navigation.py
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── callbacks.py
│   │   └── layout.py
│   ├── config
│   │   ├── __init__.py
│   │   └── paths.py
│   ├── conversion
│   │   ├── __init__.py
│   │   └── formatter.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── batch_processor.py
│   │   ├── context.py
│   │   ├── controller.py
│   │   ├── pipeline.py
│   │   └── test_batch_processor.py
│   ├── detection
│   │   ├── __init__.py
│   │   └── pdf_type_detector.py
│   ├── extraction
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── field_detection.py
│   │   ├── hybrid.py
│   │   ├── native.py
│   │   └── ocr.py
│   ├── indexer
│   │   ├── __init__.py
│   │   ├── document_text_store.py
│   │   └── inverted_index.py
│   ├── ingest
│   │   ├── __init__.py
│   │   ├── storage.py
│   │   └── uploader.py
│   ├── layout
│   │   ├── __init__.py
│   │   ├── reading_order.py
│   │   └── segmenter.py
│   ├── logs
│   │   ├── __init__.py
│   │   ├── config.example.yaml
│   │   ├── logger.py
│   │   └── test_logger.py
│   ├── metadata
│   │   ├── __init__.py
│   │   └── document_store.py
│   ├── search
│   │   ├── search_api.py
│   │   ├── search_engine.py
│   │   └── test_search_engine.py
│   ├── semantic
│   │   ├── __init__.py
│   │   ├── clustering_manager.py
│   │   ├── clustering.py
│   │   ├── embedding.py
│   │   └── field_extraction.py
│   ├── translation
│   │   ├── __init__.py
│   │   └── translator.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   └── image.py
│   ├── visualization
│   │   ├── __init__.py
│   │   └── overlay.py
│   ├── workers
│   │   ├── __init__.py
│   │   ├── test_worker_manager.py
│   │   └── worker_manager.py
│   └── __init__.py
├── tests
│   ├── conversion
│   │   └── test_formatter.py
│   ├── detection
│   │   └── test_pdf_type_detector.py
│   ├── extraction
│   │   ├── test_base.py
│   │   ├── test_hybrid.py
│   │   ├── test_native.py
│   │   ├── test_ocr_enhancements.py
│   │   └── test_ocr.py
│   ├── ingest
│   │   ├── test_storage.py
│   │   └── test_uploader.py
│   ├── layout
│   │   ├── test_reading_order.py
│   │   └── test_segmenter.py
│   ├── semantic
│   │   ├── test_clustering.py
│   │   ├── test_embedding.py
│   │   └── test_field_extraction.py
│   ├── translation
│   │   └── test_translator.py
│   ├── utils
│   │   ├── test_geometry.py
│   │   └── test_image.py
│   └── visualization
│       └── test_overlay.py
├── .gitignore
├── estructura.md
├── makefile
├── pytest.ini
├── README.md
├── requirements.txt
└── setup.cfg