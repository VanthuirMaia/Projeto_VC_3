"""
Módulo de OCR - Engines Pré-treinados
=====================================

Este módulo implementa uma interface unificada para múltiplos
engines de OCR pré-treinados, permitindo flexibilidade na escolha
e comparação de resultados.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """
    Resultado padronizado de OCR.

    Attributes:
        text: Texto reconhecido
        confidence: Confiança do reconhecimento (0-1)
        bbox: Bounding box [x1, y1, x2, y2]
        raw_bbox: Bbox original do engine (pode ter formato diferente)
    """
    text: str
    confidence: float
    bbox: List[int] = field(default_factory=list)
    raw_bbox: any = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bbox": self.bbox,
        }


class OCREngine:
    """
    Engine unificado de OCR com suporte a múltiplos backends.

    Backends suportados:
    - EasyOCR: Deep learning, bom para português
    - PaddleOCR: Estado da arte, rápido
    - Tesseract: Clássico, confiável

    Justificativa da arquitetura:
    - Interface unificada permite trocar engines facilmente
    - Ensemble de múltiplos engines aumenta precisão
    - Fallback automático em caso de falha
    """

    def __init__(self, config: dict = None):
        """
        Inicializa o engine de OCR.

        Args:
            config: Configurações do OCR
        """
        self.config = config or self._default_config()
        self._engines = {}
        self._initialize_engines()

    def _default_config(self) -> dict:
        """Retorna configurações padrão."""
        return {
            "primary_engine": "easyocr",
            "easyocr": {
                "languages": ["pt", "en"],
                "gpu": True,
                "verbose": False,
            },
            "paddleocr": {
                "lang": "pt",
                "use_angle_cls": True,
            },
            "tesseract": {
                "lang": "por",
                "config": "--oem 3 --psm 6",
            },
            "confidence_threshold": 0.5,
        }

    def _initialize_engines(self):
        """Inicializa todos os engines de OCR disponíveis."""
        # Inicializa todos os engines para permitir ensemble
        self._init_easyocr()
        self._init_paddleocr()
        self._init_tesseract()

        available = self.get_available_engines()
        logger.info(f"Engines OCR disponíveis: {available}")

    def _init_easyocr(self):
        """Inicializa EasyOCR."""
        try:
            import easyocr
            cfg = self.config.get("easyocr", {})
            self._engines["easyocr"] = easyocr.Reader(
                cfg.get("languages", ["pt", "en"]),
                gpu=cfg.get("gpu", True),
                verbose=cfg.get("verbose", False),
            )
            logger.info("EasyOCR inicializado com sucesso")
        except ImportError:
            logger.warning("EasyOCR não instalado. Use: pip install easyocr")
        except Exception as e:
            logger.error(f"Erro ao inicializar EasyOCR: {e}")

    def _init_paddleocr(self):
        """Inicializa PaddleOCR."""
        try:
            from paddleocr import PaddleOCR
            cfg = self.config.get("paddleocr", {})
            self._engines["paddleocr"] = PaddleOCR(
                lang=cfg.get("lang", "pt"),
                use_angle_cls=cfg.get("use_angle_cls", True),
                show_log=False,
            )
            logger.info("PaddleOCR inicializado com sucesso")
        except ImportError:
            logger.warning("PaddleOCR não instalado. Use: pip install paddleocr")
        except Exception as e:
            logger.error(f"Erro ao inicializar PaddleOCR: {e}")

    def _init_tesseract(self):
        """Inicializa Tesseract."""
        try:
            import pytesseract
            # Testa se Tesseract está instalado
            pytesseract.get_tesseract_version()
            self._engines["tesseract"] = pytesseract
            logger.info("Tesseract inicializado com sucesso")
        except ImportError:
            logger.warning("pytesseract não instalado. Use: pip install pytesseract")
        except Exception as e:
            logger.warning(f"Tesseract não encontrado no sistema: {e}")

    def get_available_engines(self) -> List[str]:
        """Retorna lista de engines disponíveis."""
        return list(self._engines.keys())

    def extract_text(
        self,
        image: np.ndarray,
        engine: str = None,
        detail: bool = True
    ) -> Union[str, List[OCRResult]]:
        """
        Extrai texto da imagem usando o engine especificado.

        Args:
            image: Imagem como array numpy
            engine: Engine a usar (None = usa primário)
            detail: Se True, retorna lista de OCRResult com bbox

        Returns:
            Texto extraído ou lista de OCRResult
        """
        engine = engine or self.config.get("primary_engine", "easyocr")

        if engine not in self._engines:
            available = self.get_available_engines()
            if not available:
                raise RuntimeError("Nenhum engine OCR disponível")
            engine = available[0]
            logger.warning(f"Engine {engine} não disponível, usando {engine}")

        if engine == "easyocr":
            return self._ocr_easyocr(image, detail)
        elif engine == "paddleocr":
            return self._ocr_paddleocr(image, detail)
        elif engine == "tesseract":
            return self._ocr_tesseract(image, detail)

        raise ValueError(f"Engine desconhecido: {engine}")

    def _ocr_easyocr(self, image: np.ndarray, detail: bool) -> Union[str, List[OCRResult]]:
        """Executa OCR com EasyOCR."""
        reader = self._engines["easyocr"]
        results = reader.readtext(image)

        if not detail:
            return " ".join([r[1] for r in results])

        ocr_results = []
        for bbox, text, confidence in results:
            # Converte bbox de [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] para [x1,y1,x2,y2]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            simple_bbox = [
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords))
            ]

            ocr_results.append(OCRResult(
                text=text,
                confidence=confidence,
                bbox=simple_bbox,
                raw_bbox=bbox
            ))

        return ocr_results

    def _ocr_paddleocr(self, image: np.ndarray, detail: bool) -> Union[str, List[OCRResult]]:
        """Executa OCR com PaddleOCR."""
        ocr = self._engines["paddleocr"]
        results = ocr.ocr(image, cls=True)

        if results is None or len(results) == 0:
            return "" if not detail else []

        # PaddleOCR retorna lista de listas
        results = results[0] if results else []

        if not detail:
            texts = [r[1][0] for r in results if r]
            return " ".join(texts)

        ocr_results = []
        for result in results:
            if result is None:
                continue

            bbox, (text, confidence) = result

            # Converte bbox
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            simple_bbox = [
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords))
            ]

            ocr_results.append(OCRResult(
                text=text,
                confidence=confidence,
                bbox=simple_bbox,
                raw_bbox=bbox
            ))

        return ocr_results

    def _ocr_tesseract(self, image: np.ndarray, detail: bool) -> Union[str, List[OCRResult]]:
        """Executa OCR com Tesseract."""
        import pytesseract
        cfg = self.config.get("tesseract", {})

        if not detail:
            return pytesseract.image_to_string(
                image,
                lang=cfg.get("lang", "por"),
                config=cfg.get("config", "--oem 3 --psm 6")
            )

        # Extrai dados detalhados
        data = pytesseract.image_to_data(
            image,
            lang=cfg.get("lang", "por"),
            config=cfg.get("config", "--oem 3 --psm 6"),
            output_type=pytesseract.Output.DICT
        )

        ocr_results = []
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue

            confidence = float(data['conf'][i]) / 100.0  # Normaliza para 0-1
            if confidence < 0:  # Tesseract usa -1 para erro
                confidence = 0

            bbox = [
                data['left'][i],
                data['top'][i],
                data['left'][i] + data['width'][i],
                data['top'][i] + data['height'][i]
            ]

            ocr_results.append(OCRResult(
                text=text,
                confidence=confidence,
                bbox=bbox,
            ))

        return ocr_results

    def extract_with_ensemble(
        self,
        image: np.ndarray,
        engines: List[str] = None
    ) -> Tuple[List[OCRResult], Dict[str, List[OCRResult]]]:
        """
        Executa OCR com múltiplos engines e combina resultados.

        Estratégia de ensemble:
        1. Executa OCR com cada engine disponível
        2. Combina todos os textos únicos encontrados
        3. Prioriza resultados com maior confiança
        4. Merge de bboxes sobrepostos

        Args:
            image: Imagem para OCR
            engines: Lista de engines a usar (None = todos disponíveis)

        Returns:
            Tupla (resultados combinados, resultados por engine)
        """
        engines = engines or self.get_available_engines()

        results_by_engine = {}
        for engine in engines:
            if engine in self._engines:
                try:
                    results = self.extract_text(image, engine=engine, detail=True)
                    results_by_engine[engine] = results
                    logger.info(f"{engine}: {len(results)} detecções")
                except Exception as e:
                    logger.warning(f"Erro no engine {engine}: {e}")

        # Combina resultados de todos os engines
        combined = self._merge_results(results_by_engine)

        return combined, results_by_engine

    def _merge_results(self, results_by_engine: Dict[str, List[OCRResult]]) -> List[OCRResult]:
        """
        Faz merge inteligente dos resultados de múltiplos engines.

        Estratégia:
        - Agrupa detecções por região (bbox similar)
        - Para regiões com múltiplas detecções, escolhe a de maior confiança
        - Adiciona detecções únicas de cada engine
        """
        if not results_by_engine:
            return []

        all_results = []
        seen_texts = set()

        # Coleta todos os resultados com fonte
        for engine, results in results_by_engine.items():
            for r in results:
                all_results.append((engine, r))

        # Ordena por confiança (maior primeiro)
        all_results.sort(key=lambda x: x[1].confidence, reverse=True)

        merged = []
        used_bboxes = []

        for engine, result in all_results:
            # Normaliza texto para comparação
            text_norm = result.text.strip().lower()

            # Verifica se bbox sobrepõe com algum já usado
            is_duplicate = False
            if result.bbox:
                for used_bbox in used_bboxes:
                    if self._bbox_overlap(result.bbox, used_bbox) > 0.5:
                        is_duplicate = True
                        break

            # Adiciona se não for duplicata ou se texto for novo
            if not is_duplicate or text_norm not in seen_texts:
                merged.append(result)
                seen_texts.add(text_norm)
                if result.bbox:
                    used_bboxes.append(result.bbox)

        return merged

    def _bbox_overlap(self, bbox1: List[int], bbox2: List[int]) -> float:
        """Calcula IoU (Intersection over Union) de dois bboxes."""
        if not bbox1 or not bbox2 or len(bbox1) < 4 or len(bbox2) < 4:
            return 0.0

        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def get_combined_text(self, results_by_engine: Dict[str, List[OCRResult]]) -> str:
        """
        Combina texto de múltiplos engines de forma inteligente.

        Concatena os textos únicos de cada engine, priorizando
        engines mais confiáveis.
        """
        all_texts = []
        seen_phrases = set()

        # Ordem de prioridade dos engines
        priority = ["easyocr", "paddleocr", "tesseract"]

        for engine in priority:
            if engine in results_by_engine:
                results = results_by_engine[engine]
                sorted_results = sorted(
                    results,
                    key=lambda r: (r.bbox[1], r.bbox[0]) if r.bbox else (0, 0)
                )
                for r in sorted_results:
                    text = r.text.strip()
                    # Evita duplicatas exatas
                    if text.lower() not in seen_phrases and len(text) > 1:
                        all_texts.append(text)
                        seen_phrases.add(text.lower())

        return " ".join(all_texts)

    def filter_by_confidence(
        self,
        results: List[OCRResult],
        threshold: float = None
    ) -> List[OCRResult]:
        """
        Filtra resultados por confiança mínima.

        Args:
            results: Lista de resultados OCR
            threshold: Limiar de confiança (0-1)

        Returns:
            Resultados filtrados
        """
        threshold = threshold or self.config.get("confidence_threshold", 0.5)
        return [r for r in results if r.confidence >= threshold]

    def get_full_text(self, results: List[OCRResult]) -> str:
        """
        Concatena todos os textos dos resultados.

        Args:
            results: Lista de resultados OCR

        Returns:
            Texto completo concatenado
        """
        # Ordena por posição (top-left primeiro)
        sorted_results = sorted(results, key=lambda r: (r.bbox[1], r.bbox[0]) if r.bbox else (0, 0))
        return " ".join([r.text for r in sorted_results])
