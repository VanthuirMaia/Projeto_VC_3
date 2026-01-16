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

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"}
MAX_FILE_SIZE = API_CONFIG.get("max_upload_size_mb", 10) * 1024 * 1024


async def validate_and_load_image(file: UploadFile) -> np.ndarray:
    """
    Valida e carrega imagem do upload.

    Args:
        file: Arquivo enviado

    Returns:
        Imagem como array numpy

    Raises:
        HTTPException: Se arquivo inválido
    """
    # Verifica extensão
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

    # Carrega imagem
    try:
        image = Image.open(io.BytesIO(contents))
        # Converte para RGB se necessário
        if image.mode != "RGB":
            image = image.convert("RGB")
        return np.array(image)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao carregar imagem: {str(e)}"
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
    file: UploadFile = File(..., description="Imagem da Nota Fiscal"),
    engine: Optional[str] = Query(None, description="Engine OCR a usar"),
    preprocess: bool = Query(True, description="Aplicar pré-processamento"),
):
    """
    Realiza OCR na imagem e retorna texto bruto.

    - **file**: Imagem para processar (JPG, PNG, etc.)
    - **engine**: Engine OCR (easyocr, paddleocr, tesseract). Padrão: primário configurado
    - **preprocess**: Se deve aplicar pré-processamento
    """
    try:
        # Carrega imagem
        image = await validate_and_load_image(file)

        # Pré-processamento
        processor = get_image_processor()
        if preprocess:
            image = processor.process_for_ocr(image, binarize=False)

        # OCR
        ocr = get_ocr_engine()
        results = ocr.extract_text(image, engine=engine, detail=True)

        # Filtra por confiança
        results = ocr.filter_by_confidence(results)

        # Monta resposta
        detections = [
            OCRResultModel(
                text=r.text,
                confidence=r.confidence,
                bbox=r.bbox
            )
            for r in results
        ]

        return OCRResponse(
            success=True,
            text=ocr.get_full_text(results),
            detections=detections,
            engine_used=engine or OCR_CONFIG.get("primary_engine", "easyocr")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract", response_model=ExtractResponse)
async def extract_nf_data(
    file: UploadFile = File(..., description="Imagem da Nota Fiscal"),
    engine: Optional[str] = Query(None, description="Engine OCR a usar"),
    include_raw_text: bool = Query(False, description="Incluir texto OCR bruto na resposta"),
):
    """
    Extrai dados estruturados da Nota Fiscal.

    Pipeline completo:
    1. Pré-processamento da imagem
    2. OCR para extração de texto
    3. Extração de campos (CNPJ, valores, etc.)
    4. Validação e formatação

    - **file**: Imagem da NF (JPG, PNG, etc.)
    - **engine**: Engine OCR a usar
    - **include_raw_text**: Se deve incluir texto bruto na resposta
    """
    try:
        # 1. Carrega imagem
        image = await validate_and_load_image(file)
        original_shape = image.shape

        # 2. Pré-processamento
        processor = get_image_processor()
        processed_image = processor.process_for_ocr(image, binarize=False)
        processed_shape = processed_image.shape

        # 3. OCR
        ocr = get_ocr_engine()
        ocr_results = ocr.extract_text(processed_image, engine=engine, detail=True)
        filtered_results = ocr.filter_by_confidence(ocr_results)
        full_text = ocr.get_full_text(filtered_results)

        # 4. Extração de campos
        extractor = get_nf_extractor()
        nf_data = extractor.extract(full_text)

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
            "original_size": list(original_shape[:2]),
            "processed_size": list(processed_shape[:2]) if len(processed_shape) >= 2 else list(processed_shape),
            "ocr_engine": engine or OCR_CONFIG.get("primary_engine", "easyocr"),
            "total_detections": len(ocr_results),
            "filtered_detections": len(filtered_results),
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
