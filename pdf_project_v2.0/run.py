"""
run.py — Punto de entrada de la aplicación PDF Extractor.
Ejecutar con: python run.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.app.app import app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
