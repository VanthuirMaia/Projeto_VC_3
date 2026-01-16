"""
Pipeline OCR para Notas Fiscais
===============================

Sistema de extração de dados de Notas Fiscais brasileiras
utilizando OCR com modelos pré-treinados.

Módulos:
- preprocessing: Tratamento de imagens
- ocr: Engines de OCR (EasyOCR, PaddleOCR, Tesseract)
- extraction: Extração de campos estruturados
- api: API REST FastAPI
"""

from .preprocessing import ImageProcessor
from .ocr import OCREngine, OCRResult
from .extraction import NFExtractor, NFData

__version__ = "1.0.0"
__all__ = [
    "ImageProcessor",
    "OCREngine",
    "OCRResult",
    "NFExtractor",
    "NFData",
]
