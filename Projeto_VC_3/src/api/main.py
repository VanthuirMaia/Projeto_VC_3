"""
API REST para OCR de Notas Fiscais
==================================

Backend em FastAPI para processamento de imagens de Notas Fiscais
e extração de dados estruturados via OCR.

Endpoints:
- POST /extract: Upload de imagem e extração de dados
- POST /ocr: Apenas OCR (texto bruto)
- GET /health: Health check

"""

import io
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import numpy as np
from PIL import Image

# Imports do projeto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing import ImageProcessor
from src.ocr import OCREngine, OCRResult
from src.extraction import NFExtractor, NFData
from src.config import API_CONFIG, PREPROCESSING_CONFIG, OCR_CONFIG, EXTRACTION_CONFIG

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class OCRResultModel(BaseModel):
    """Modelo de resposta para resultado OCR."""
    text: str
    confidence: float
    bbox: List[int] = []


class OCRResponse(BaseModel):
    """Resposta do endpoint de OCR."""
    success: bool
    text: str
    detections: List[OCRResultModel] = []
    engine_used: str
    engines_results: dict = {}  # Resultados por engine quando usa ensemble


class NFItemModel(BaseModel):
    """Modelo para item da NF."""
    codigo: str = ""
    descricao: str = ""
    quantidade: float = 0.0
    unidade: str = ""
    valor_unitario: float = 0.0
    valor_total: float = 0.0


class NFDataModel(BaseModel):
    """Modelo de resposta para dados da NF."""
    numero_nf: str = ""
    serie: str = ""
    chave_acesso: str = ""
    data_emissao: str = ""

    cnpj_emitente: str = ""
    razao_social_emitente: str = ""
    inscricao_estadual_emitente: str = ""

    cnpj_destinatario: str = ""
    cpf_destinatario: str = ""
    nome_destinatario: str = ""

    valor_total: float = 0.0
    valor_produtos: float = 0.0
    valor_frete: float = 0.0
    valor_icms: float = 0.0

    itens: List[NFItemModel] = []

    confidence_score: float = 0.0
    campos_extraidos: int = 0


class ExtractResponse(BaseModel):
    """Resposta completa do endpoint de extração."""
    success: bool
    data: NFDataModel
    raw_text: str = ""
    processing_info: dict = {}


class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str
    version: str
    ocr_engines: List[str]


# =============================================================================
# INICIALIZAÇÃO DA API
# =============================================================================

app = FastAPI(
    title=API_CONFIG.get("title", "API OCR Notas Fiscais"),
    description=API_CONFIG.get("description", "API para extração de dados de NFs via OCR"),
    version=API_CONFIG.get("version", "1.0.0"),
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Componentes do pipeline (inicializados sob demanda)
_image_processor: Optional[ImageProcessor] = None
_ocr_engine: Optional[OCREngine] = None
_nf_extractor: Optional[NFExtractor] = None


def get_image_processor() -> ImageProcessor:
    """Retorna instância do processador de imagens."""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor(PREPROCESSING_CONFIG)
    return _image_processor


def get_ocr_engine() -> OCREngine:
    """Retorna instância do engine OCR."""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine(OCR_CONFIG)
    return _ocr_engine


def get_nf_extractor() -> NFExtractor:
    """Retorna instância do extrator de NF."""
    global _nf_extractor
    if _nf_extractor is None:
        _nf_extractor = NFExtractor(EXTRACTION_CONFIG)
    return _nf_extractor


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif", ".pdf"}
MAX_FILE_SIZE = API_CONFIG.get("max_upload_size_mb", 10) * 1024 * 1024


async def validate_and_load_file(file: UploadFile) -> tuple[List[np.ndarray], bool]:
    """
    Valida e carrega imagem ou PDF do upload.

    Args:
        file: Arquivo enviado

    Returns:
        Tupla (lista de imagens, is_pdf)

    Raises:
        HTTPException: Se arquivo inválido
    """
    # Verifica extensão
    ext = ""
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado: {ext}. Use: {ALLOWED_EXTENSIONS}"
            )

    # Lê conteúdo
    contents = await file.read()

    # Verifica tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    is_pdf = ext == ".pdf" or contents[:4] == b'%PDF'

    # Carrega arquivo
    try:
        if is_pdf:
            processor = get_image_processor()
            images = processor.load_pdf_from_bytes(contents)
            if not images:
                raise HTTPException(status_code=400, detail="PDF vazio ou inválido")
            return images, True  # Retorna todas as páginas
        else:
            image = Image.open(io.BytesIO(contents))
            if image.mode != "RGB":
                image = image.convert("RGB")
            return [np.array(image)], False  # Retorna como lista
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao carregar arquivo: {str(e)}"
        )


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check e informações da API.

    Retorna status e engines OCR disponíveis.
    """
    ocr = get_ocr_engine()
    return HealthResponse(
        status="healthy",
        version=API_CONFIG.get("version", "1.0.0"),
        ocr_engines=ocr.get_available_engines()
    )


@app.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(..., description="Imagem ou PDF da Nota Fiscal"),
    engine: Optional[str] = Query("ensemble", description="Engine OCR ('easyocr', 'paddleocr', 'tesseract') ou 'ensemble' para usar todos (recomendado)"),
    preprocess: bool = Query(True, description="Aplicar pré-processamento"),
    use_enhancements: bool = Query(True, description="Aplicar melhorias avançadas de imagem"),
    use_postprocessing: bool = Query(True, description="Aplicar pós-processamento de texto"),
):
    """
    Realiza OCR na imagem/PDF e retorna texto bruto.

    Para PDFs, processa todas as páginas e concatena o texto.

    **Recomendado:** Use engine='ensemble' para melhor precisão.

    - **file**: Arquivo para processar (JPG, PNG, PDF, etc.)
    - **engine**: 'ensemble' (recomendado) ou engine específico
    - **preprocess**: Se deve aplicar pré-processamento básico
    - **use_enhancements**: Se deve aplicar melhorias avançadas de imagem
    - **use_postprocessing**: Se deve aplicar pós-processamento de texto
    """
    try:
        # Carrega imagens (pode ser múltiplas páginas de PDF)
        images, is_pdf = await validate_and_load_file(file)

        processor = get_image_processor()
        ocr = get_ocr_engine()

        # Garante que use ensemble por padrão (se None, vazio ou "ensemble")
        if engine is None or engine == "" or engine == "ensemble":
            use_ensemble = True
            engine = "ensemble"  # Normaliza para garantir consistência
        else:
            use_ensemble = False
        
        all_results = []
        all_texts = []
        engines_summary = {}

        # Processa cada página/imagem
        for page_num, image in enumerate(images):
            # Pré-processamento básico
            if preprocess:
                processed_image = processor.process_for_ocr(image, binarize=False)
            else:
                processed_image = image
            
            # Melhorias avançadas (se habilitado)
            if use_enhancements:
                try:
                    from src.preprocessing.image_enhancer import ImageEnhancer
                    enhancer = ImageEnhancer()
                    # Avalia qualidade e aplica melhorias adaptativas
                    quality = enhancer.assess_image_quality(processed_image)
                    if quality.get("is_blurry") or quality.get("is_low_contrast"):
                        processed_image = enhancer.enhance_for_ocr(processed_image, use_adaptive=True)
                except ImportError:
                    pass  # Módulo opcional
                except Exception as e:
                    logger.warning(f"Erro ao aplicar melhorias de imagem: {e}")

            if use_ensemble:
                # Usa múltiplos engines
                combined, results_by_engine = ocr.extract_with_ensemble(processed_image)
                filtered = ocr.filter_by_confidence(combined)
                all_results.extend(filtered)

                # Combina texto de todos os engines (com pós-processamento se habilitado)
                page_text = ocr.get_combined_text(results_by_engine, use_postprocessing=use_postprocessing)
                all_texts.append(page_text)

                # Sumariza resultados por engine
                for eng, res in results_by_engine.items():
                    if eng not in engines_summary:
                        engines_summary[eng] = {"detections": 0, "sample_texts": []}
                    engines_summary[eng]["detections"] += len(res)
                    # Adiciona alguns textos de exemplo
                    for r in res[:3]:
                        if r.text not in engines_summary[eng]["sample_texts"]:
                            engines_summary[eng]["sample_texts"].append(r.text)
            else:
                # Usa engine único
                results = ocr.extract_text(processed_image, engine=engine, detail=True)
                filtered = ocr.filter_by_confidence(results)
                all_results.extend(filtered)
                
                # Aplica pós-processamento se habilitado
                if use_postprocessing:
                    try:
                        from src.ocr.text_postprocessor import TextPostProcessor
                        postprocessor = TextPostProcessor()
                        raw_text = ocr.get_full_text(filtered)
                        processed_text = postprocessor.process(raw_text, apply_all=True)
                        all_texts.append(processed_text)
                    except ImportError:
                        all_texts.append(ocr.get_full_text(filtered))
                else:
                    all_texts.append(ocr.get_full_text(filtered))

        # Monta resposta
        detections = [
            OCRResultModel(
                text=r.text,
                confidence=r.confidence,
                bbox=r.bbox
            )
            for r in all_results
        ]

        # Junta texto de todas as páginas
        full_text = "\n\n".join(all_texts)

        return OCRResponse(
            success=True,
            text=full_text,
            detections=detections,
            engine_used="ensemble" if use_ensemble else (engine or "ensemble"),
            engines_results=engines_summary if use_ensemble else {}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract", response_model=ExtractResponse)
async def extract_nf_data(
    file: UploadFile = File(..., description="Imagem ou PDF da Nota Fiscal"),
    engine: Optional[str] = Query("ensemble", description="Engine OCR ('easyocr', 'paddleocr', 'tesseract') ou 'ensemble' para usar todos (recomendado)"),
    include_raw_text: bool = Query(False, description="Incluir texto OCR bruto na resposta"),
):
    """
    Extrai dados estruturados da Nota Fiscal.

    Para PDFs, processa todas as páginas e extrai dados do texto combinado.

    **Recomendado:** Use engine='ensemble' para combinar múltiplos OCRs e melhorar precisão.

    Pipeline completo:
    1. Pré-processamento da imagem/PDF (todas as páginas)
    2. OCR para extração de texto (ensemble combina EasyOCR + PaddleOCR + Tesseract)
    3. Extração de campos (CNPJ, valores, etc.)
    4. Validação e formatação

    - **file**: Arquivo da NF (JPG, PNG, PDF, etc.)
    - **engine**: 'ensemble' (recomendado) ou engine específico
    - **include_raw_text**: Se deve incluir texto bruto na resposta
    """
    try:
        # 1. Carrega imagens (pode ser múltiplas páginas de PDF)
        images, is_pdf = await validate_and_load_file(file)

        processor = get_image_processor()
        ocr = get_ocr_engine()

        # Garante que use ensemble por padrão
        if engine is None or engine == "" or engine == "ensemble":
            use_ensemble = True
            engine = "ensemble"  # Normaliza para garantir consistência
        else:
            use_ensemble = False
        
        all_texts = []
        total_detections = 0
        filtered_detections = 0
        engines_used = []
        all_ocr_confidences = []  # Armazena confianças do OCR para calcular média

        # 2. Processa cada página
        for page_num, image in enumerate(images):
            # Pré-processamento básico
            processed_image = processor.process_for_ocr(image, binarize=False)
            
            # Melhorias avançadas (se disponível)
            try:
                from src.preprocessing.image_enhancer import ImageEnhancer
                enhancer = ImageEnhancer()
                # Avalia qualidade e aplica melhorias adaptativas
                quality = enhancer.assess_image_quality(processed_image)
                if quality.get("is_blurry") or quality.get("is_low_contrast"):
                    processed_image = enhancer.enhance_for_ocr(processed_image, use_adaptive=True)
            except ImportError:
                pass  # Módulo opcional
            except Exception as e:
                logger.warning(f"Erro ao aplicar melhorias de imagem: {e}")

            if use_ensemble:
                # Usa múltiplos engines combinados
                combined, results_by_engine = ocr.extract_with_ensemble(processed_image)
                filtered_results = ocr.filter_by_confidence(combined)

                total_detections += len(combined)
                filtered_detections += len(filtered_results)
                
                # Coleta confianças do OCR para cálculo de média
                for result in filtered_results:
                    all_ocr_confidences.append(result.confidence)

                # Combina texto de todos os engines (com pós-processamento)
                page_text = ocr.get_combined_text(results_by_engine, use_postprocessing=True)
                all_texts.append(page_text)

                engines_used = list(results_by_engine.keys())
            else:
                # Usa engine único
                ocr_results = ocr.extract_text(processed_image, engine=engine, detail=True)
                filtered_results = ocr.filter_by_confidence(ocr_results)

                total_detections += len(ocr_results)
                filtered_detections += len(filtered_results)
                
                # Coleta confianças do OCR
                for result in filtered_results:
                    all_ocr_confidences.append(result.confidence)

                page_text = ocr.get_full_text(filtered_results)
                all_texts.append(page_text)

        # 3. Combina texto de todas as páginas
        full_text = "\n\n".join(all_texts)

        # 4. Calcula confiança média do OCR
        ocr_confidence_avg = 0.0
        if all_ocr_confidences:
            ocr_confidence_avg = sum(all_ocr_confidences) / len(all_ocr_confidences)

        # 5. Extração de campos
        extractor = get_nf_extractor()
        nf_data = extractor.extract(full_text)
        
        # 6. Melhora o cálculo de confiança combinando OCR + campos extraídos
        # Combina confiança do OCR (peso 70%) com proporção de campos (peso 30%)
        campos_ratio = nf_data.campos_extraidos / nf_data.campos_total if nf_data.campos_total > 0 else 0
        nf_data.confidence_score = (ocr_confidence_avg * 0.7) + (campos_ratio * 0.3)

        # 5. Monta resposta
        nf_model = NFDataModel(
            numero_nf=nf_data.numero_nf,
            serie=nf_data.serie,
            chave_acesso=nf_data.chave_acesso,
            data_emissao=nf_data.data_emissao,
            cnpj_emitente=nf_data.cnpj_emitente,
            razao_social_emitente=nf_data.razao_social_emitente,
            inscricao_estadual_emitente=nf_data.inscricao_estadual_emitente,
            cnpj_destinatario=nf_data.cnpj_destinatario,
            cpf_destinatario=nf_data.cpf_destinatario,
            nome_destinatario=nf_data.nome_destinatario,
            valor_total=nf_data.valor_total,
            valor_produtos=nf_data.valor_produtos,
            valor_frete=nf_data.valor_frete,
            valor_icms=nf_data.valor_icms,
            confidence_score=nf_data.confidence_score,
            campos_extraidos=nf_data.campos_extraidos,
        )

        processing_info = {
            "pages_processed": len(images),
            "is_pdf": is_pdf,
            "ocr_engine": "ensemble" if use_ensemble else (engine or OCR_CONFIG.get("primary_engine", "easyocr")),
            "engines_used": engines_used if use_ensemble else [engine or OCR_CONFIG.get("primary_engine", "easyocr")],
            "total_detections": total_detections,
            "filtered_detections": filtered_detections,
            "ocr_confidence_avg": float(ocr_confidence_avg),  # Confiança média do OCR
        }

        return ExtractResponse(
            success=True,
            data=nf_model,
            raw_text=full_text if include_raw_text else "",
            processing_info=processing_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_CONFIG.get("host", "0.0.0.0"),
        port=API_CONFIG.get("port", 8000),
        reload=True
    )
