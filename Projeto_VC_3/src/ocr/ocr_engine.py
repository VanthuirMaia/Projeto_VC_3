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
import re

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
            # Parâmetros do PaddleOCR
            # Nota: use_angle_cls foi substituído por use_textline_orientation nas versões recentes
            paddle_params = {
                "lang": cfg.get("lang", "pt"),
            }
            # Usa use_textline_orientation se disponível (versões recentes)
            # Fallback para use_angle_cls em versões antigas
            use_textline_orientation = cfg.get("use_textline_orientation")
            use_angle_cls = cfg.get("use_angle_cls")
            
            if use_textline_orientation is not None:
                paddle_params["use_textline_orientation"] = use_textline_orientation
            elif use_angle_cls is not None:
                # Mantém compatibilidade com versões antigas (pode gerar deprecation warning)
                paddle_params["use_angle_cls"] = use_angle_cls
            else:
                # Padrão: tenta usar parâmetro moderno
                paddle_params["use_textline_orientation"] = True
            
            # Não adiciona use_gpu - versões recentes detectam GPU automaticamente
            # Se precisar forçar CPU, use: use_pdserving=False
            
            self._engines["paddleocr"] = PaddleOCR(**paddle_params)
            logger.info("PaddleOCR inicializado com sucesso")
        except ImportError:
            logger.warning("PaddleOCR não instalado. Use: pip install paddleocr paddlepaddle")
        except Exception as e:
            logger.error(f"Erro ao inicializar PaddleOCR: {e}", exc_info=True)

    def _init_tesseract(self):
        """Inicializa Tesseract."""
        try:
            import pytesseract
            import platform
            import os
            
            # Obtém configuração do Tesseract
            cfg = self.config.get("tesseract", {})
            tesseract_cmd = cfg.get("tesseract_cmd")
            
            # Se caminho especificado, configura
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                logger.info(f"Tesseract configurado manualmente: {tesseract_cmd}")
                
                # Configura TESSDATA_PREFIX para encontrar idiomas
                tesseract_dir = os.path.dirname(tesseract_cmd)
                tessdata_dir = os.path.join(tesseract_dir, "tessdata")
                if os.path.exists(tessdata_dir):
                    os.environ["TESSDATA_PREFIX"] = tessdata_dir
                    logger.info(f"TESSDATA_PREFIX configurado: {tessdata_dir}")
            else:
                # Tenta detecção automática (especialmente no Windows)
                if platform.system() == "Windows":
                    # Caminhos comuns no Windows
                    common_paths = [
                        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
                        r"C:\tesseract\tesseract.exe",
                    ]
                    
                    # Verifica se algum caminho existe
                    for path in common_paths:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            logger.info(f"Tesseract detectado automaticamente: {path}")
                            # Configura TESSDATA_PREFIX
                            tesseract_dir = os.path.dirname(path)
                            tessdata_dir = os.path.join(tesseract_dir, "tessdata")
                            if os.path.exists(tessdata_dir):
                                os.environ["TESSDATA_PREFIX"] = tessdata_dir
                                logger.info(f"TESSDATA_PREFIX configurado: {tessdata_dir}")
                            break
                    else:
                        # Tenta encontrar no PATH
                        try:
                            pytesseract.get_tesseract_version()
                            logger.info("Tesseract encontrado no PATH")
                        except:
                            logger.warning(
                                "Tesseract não encontrado automaticamente no Windows. "
                                "Configure manualmente em config.py: tesseract_cmd = r'C:\\...\\tesseract.exe'"
                            )
            
            # Configura TESSDATA_PREFIX se ainda não foi configurado
            if "TESSDATA_PREFIX" not in os.environ:
                # Tenta encontrar tessdata automaticamente
                tesseract_dir = os.path.dirname(pytesseract.pytesseract.tesseract_cmd) if hasattr(pytesseract.pytesseract, 'tesseract_cmd') and pytesseract.pytesseract.tesseract_cmd else None
                if not tesseract_dir or not os.path.exists(tesseract_dir):
                    # Caminhos comuns
                    for common_dir in [r"C:\Program Files\Tesseract-OCR", r"C:\Program Files (x86)\Tesseract-OCR"]:
                        tessdata_path = os.path.join(common_dir, "tessdata")
                        if os.path.exists(tessdata_path):
                            os.environ["TESSDATA_PREFIX"] = tessdata_path
                            logger.info(f"TESSDATA_PREFIX configurado automaticamente: {tessdata_path}")
                            break
                elif tesseract_dir:
                    tessdata_path = os.path.join(tesseract_dir, "tessdata")
                    if os.path.exists(tessdata_path):
                        os.environ["TESSDATA_PREFIX"] = tessdata_path
            
            # Testa se Tesseract está funcionando
            version = pytesseract.get_tesseract_version()
            self._engines["tesseract"] = pytesseract
            logger.info(f"Tesseract inicializado com sucesso (versão: {version})")
            
            # Verifica idioma português
            try:
                langs = pytesseract.get_languages(config='')
                if 'por' not in langs:
                    logger.warning("Idioma português (por) não encontrado. Baixe por.traineddata e coloque em tessdata/")
            except:
                logger.warning("Não foi possível verificar idiomas do Tesseract")
            
        except ImportError:
            logger.warning("pytesseract não instalado. Use: pip install pytesseract")
        except Exception as e:
            logger.warning(f"Tesseract não encontrado no sistema: {e}")
            logger.warning(
                "Para instalar o Tesseract:\n"
                "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  Linux: sudo apt-get install tesseract-ocr tesseract-ocr-por\n"
                "  Mac: brew install tesseract tesseract-lang"
            )

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
        Faz merge inteligente dos resultados de múltiplos engines com votação ponderada.

        Estratégia melhorada:
        - Agrupa detecções por região (bbox similar)
        - Votação ponderada por confiança e engine
        - Para regiões com múltiplas detecções, escolhe por consenso
        - Adiciona detecções únicas de cada engine
        - Pesos por engine: EasyOCR=0.4, PaddleOCR=0.4, Tesseract=0.2
        """
        if not results_by_engine:
            return []

        # Pesos por engine (baseado em performance típica)
        engine_weights = {
            "easyocr": 0.4,
            "paddleocr": 0.4,
            "tesseract": 0.2,
        }

        all_results = []
        seen_texts = set()

        # Coleta todos os resultados com fonte e peso
        for engine, results in results_by_engine.items():
            weight = engine_weights.get(engine, 0.3)
            for r in results:
                # Score combinado: confiança * peso do engine
                combined_score = r.confidence * weight
                all_results.append((engine, r, combined_score))

        # Ordena por score combinado (maior primeiro)
        all_results.sort(key=lambda x: x[2], reverse=True)

        merged = []
        used_bboxes = []
        # Agrupa resultados por região para votação
        region_groups = {}

        for engine, result, score in all_results:
            if not result.bbox or len(result.bbox) < 4:
                # Sem bbox, adiciona diretamente se texto for único
                text_norm = result.text.strip().lower()
                if text_norm and text_norm not in seen_texts:
                    merged.append(result)
                    seen_texts.add(text_norm)
                continue

            # Encontra grupo de região similar
            grouped = False
            for region_key, group_results in region_groups.items():
                # Verifica se bbox está na mesma região
                if self._bbox_overlap(result.bbox, region_key) > 0.3:
                    group_results.append((engine, result, score))
                    grouped = True
                    break

            if not grouped:
                # Nova região
                region_groups[tuple(result.bbox)] = [(engine, result, score)]

        # Processa cada grupo de região
        for region_key, group_results in region_groups.items():
            if len(group_results) == 1:
                # Única detecção na região
                _, result, _ = group_results[0]
                text_norm = result.text.strip().lower()
                if text_norm and text_norm not in seen_texts:
                    merged.append(result)
                    seen_texts.add(text_norm)
                    used_bboxes.append(list(region_key))
            else:
                # Múltiplas detecções - votação ponderada
                # Agrupa por texto similar
                text_groups = {}
                for engine, result, score in group_results:
                    text_norm = result.text.strip().lower()
                    # Normaliza texto para agrupamento (remove espaços extras)
                    text_key = re.sub(r'\s+', ' ', text_norm)
                    
                    if text_key not in text_groups:
                        text_groups[text_key] = []
                    text_groups[text_key].append((engine, result, score))

                # Escolhe texto com maior score total
                best_text = None
                best_score = 0
                best_result = None

                for text_key, text_results in text_groups.items():
                    # Soma scores ponderados
                    total_score = sum(score for _, _, score in text_results)
                    # Bônus se múltiplos engines concordam
                    consensus_bonus = len(text_results) * 0.1
                    final_score = total_score + consensus_bonus

                    if final_score > best_score:
                        best_score = final_score
                        # Escolhe resultado com maior confiança individual
                        best_result = max(text_results, key=lambda x: x[1].confidence)[1]
                        best_text = text_key

                if best_result and best_text not in seen_texts:
                    # Ajusta confiança baseada em consenso
                    consensus_count = len(text_groups.get(best_text, []))
                    if consensus_count > 1:
                        # Múltiplos engines concordam - aumenta confiança
                        best_result.confidence = min(1.0, best_result.confidence * 1.1)
                    
                    merged.append(best_result)
                    seen_texts.add(best_text)
                    used_bboxes.append(list(region_key))

        # Ordena resultados por posição (top-left primeiro)
        merged.sort(key=lambda r: (r.bbox[1], r.bbox[0]) if r.bbox else (0, 0))

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

    def get_combined_text(
        self,
        results_by_engine: Dict[str, List[OCRResult]],
        use_postprocessing: bool = True
    ) -> str:
        """
        Combina texto de múltiplos engines de forma inteligente.

        Concatena os textos únicos de cada engine, priorizando
        engines mais confiáveis e aplicando pós-processamento.
        
        Args:
            results_by_engine: Resultados por engine
            use_postprocessing: Se True, aplica pós-processamento
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

        combined = " ".join(all_texts)
        
        # Aplica pós-processamento se habilitado
        if use_postprocessing:
            try:
                from src.ocr.text_postprocessor import TextPostProcessor
                postprocessor = TextPostProcessor()
                combined = postprocessor.process(combined, apply_all=True)
            except ImportError:
                logger.warning("TextPostProcessor não disponível, pulando pós-processamento")
            except Exception as e:
                logger.warning(f"Erro no pós-processamento: {e}")

        return combined

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
