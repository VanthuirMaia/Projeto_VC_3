"""
Configurações do Pipeline OCR para Notas Fiscais
=================================================

Este arquivo contém todas as configurações do pipeline,
com justificativas técnicas para cada escolha.
"""

from pathlib import Path
from typing import List, Dict

# =============================================================================
# CAMINHOS DO PROJETO
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# =============================================================================
# 1. BASE DE DADOS / SAMPLES
# =============================================================================
"""
JUSTIFICATIVA - BASE DE DADOS:

Para este projeto de OCR em Notas Fiscais, não utilizamos um dataset de
treinamento tradicional, pois empregamos modelos OCR pré-treinados.

No entanto, para validação e demonstração, utilizamos:

1. SAMPLES DE NOTAS FISCAIS:
   - Notas Fiscais Eletrônicas (NF-e) brasileiras
   - Formato DANFE (Documento Auxiliar da Nota Fiscal Eletrônica)
   - Variações: diferentes emissores, layouts, qualidades de impressão

2. CARACTERÍSTICAS DO DANFE:
   - Layout padronizado pela legislação brasileira
   - Campos obrigatórios bem definidos (CNPJ, valores, itens, etc.)
   - Código de barras e QR Code
   - Estrutura tabular previsível

3. POR QUE NÃO TREINAR UM MODELO PRÓPRIO:
   - Modelos OCR modernos (EasyOCR, PaddleOCR) já são treinados em
     milhões de imagens de texto em múltiplos idiomas
   - O desafio está na EXTRAÇÃO ESTRUTURADA, não no reconhecimento
   - Fine-tuning seria necessário apenas para fontes muito específicas

4. FONTES DE DADOS PARA TESTES:
   - Imagens de exemplo de DANFEs (domínio público)
   - Notas fiscais sintéticas geradas para teste
   - Uploads do usuário via API
"""

DATA_CONFIG = {
    "supported_formats": [".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".bmp"],
    "max_file_size_mb": 10,
    "sample_images_dir": SAMPLES_DIR,
}

# =============================================================================
# 2. TÉCNICAS DE PRÉ-PROCESSAMENTO DE IMAGENS
# =============================================================================
"""
JUSTIFICATIVA - TÉCNICAS DE TRATAMENTO DE IMAGENS:

O pré-processamento é CRUCIAL para OCR de documentos. Aplicamos:

1. CONVERSÃO PARA ESCALA DE CINZA:
   - Reduz complexidade (3 canais -> 1 canal)
   - Remove informação de cor irrelevante para texto
   - Acelera processamento subsequente

2. REDIMENSIONAMENTO ADAPTATIVO:
   - Mínimo 300 DPI equivalente para boa leitura
   - Upscaling de imagens pequenas melhora precisão do OCR
   - Downscaling de imagens muito grandes economiza memória

3. BINARIZAÇÃO (THRESHOLDING):
   - Otsu's Method: automático, bom para documentos uniformes
   - Adaptive Threshold: melhor para iluminação irregular
   - Separa texto do fundo de forma clara

4. REMOÇÃO DE RUÍDO:
   - Gaussian Blur leve antes da binarização
   - Morphological operations (opening/closing)
   - Remove artefatos de digitalização

5. CORREÇÃO DE INCLINAÇÃO (DESKEW):
   - Detecta ângulo de rotação via Hough Transform
   - Corrige documentos escaneados tortos
   - Melhora significativamente a precisão do OCR

6. CORREÇÃO DE PERSPECTIVA:
   - Detecta bordas do documento
   - Aplica transformação de perspectiva
   - Útil para fotos de documentos (não scans)

7. AUMENTO DE CONTRASTE:
   - CLAHE (Contrast Limited Adaptive Histogram Equalization)
   - Melhora legibilidade de documentos desbotados
   - Preserva detalhes locais
"""

PREPROCESSING_CONFIG = {
    # Redimensionamento
    "target_dpi": 300,
    "min_width": 1000,
    "max_width": 4000,

    # Binarização
    "binarization_method": "adaptive",  # "otsu", "adaptive", "sauvola"
    "adaptive_block_size": 11,
    "adaptive_c": 2,

    # Remoção de ruído
    "denoise": True,
    "denoise_strength": 10,

    # Correção de inclinação
    "deskew": True,
    "deskew_max_angle": 10,  # graus

    # Contraste
    "enhance_contrast": True,
    "clahe_clip_limit": 2.0,
    "clahe_grid_size": (8, 8),
}

# =============================================================================
# 3. MODELOS OCR PRÉ-TREINADOS
# =============================================================================
"""
JUSTIFICATIVA - ESCOLHA DOS MODELOS OCR:

Utilizamos uma combinação de engines OCR pré-treinados:

1. EASYOCR (MODELO PRINCIPAL):
   Justificativa:
   - Baseado em Deep Learning (CRAFT + CRNN)
   - Excelente suporte a português brasileiro
   - Detecta texto em ângulos variados
   - Bom desempenho em documentos com ruído
   - GPU acceleration disponível
   - Open source e gratuito

   Arquitetura:
   - Detector: CRAFT (Character Region Awareness for Text)
   - Reconhecedor: CRNN (CNN + BiLSTM + CTC)

   Métricas típicas:
   - Precisão em texto impresso: 95-98%
   - Suporte a 80+ idiomas

2. PADDLEOCR (ALTERNATIVA):
   Justificativa:
   - Desenvolvido pela Baidu, estado da arte
   - PP-OCR v4: detector + reconhecedor otimizados
   - Muito rápido e preciso
   - Bom para tabelas e layouts estruturados

3. TESSERACT (FALLBACK):
   Justificativa:
   - Engine tradicional, mantido pelo Google
   - Confiável e bem documentado
   - Útil como fallback ou validação
   - LSTM-based desde v4.0

ESTRATÉGIA DE ENSEMBLE:
- Usar EasyOCR como principal
- PaddleOCR para regiões tabulares
- Comparar resultados para maior confiança
"""

OCR_CONFIG = {
    # Engine principal
    "primary_engine": "easyocr",

    # Configurações EasyOCR
    "easyocr": {
        "languages": ["pt", "en"],  # Português + Inglês para termos técnicos
        "gpu": True,  # Usar GPU se disponível
        "model_storage_directory": None,  # Usa padrão
        "download_enabled": True,
        "detector": True,
        "recognizer": True,
        "verbose": False,
        "quantize": True,  # Quantização para menor uso de memória
    },

    # Configurações PaddleOCR
    "paddleocr": {
        "lang": "pt",
        "use_gpu": True,
        "use_angle_cls": True,  # Classificador de ângulo
        "det_db_thresh": 0.3,
        "det_db_box_thresh": 0.5,
    },

    # Configurações Tesseract
    "tesseract": {
        "lang": "por",  # Português
        "config": "--oem 3 --psm 6",  # LSTM OCR, assume bloco de texto
        # Caminho do executável Tesseract (None = detecção automática)
        # Windows exemplo: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        # Linux/Mac: geralmente em PATH, mas pode ser "/usr/bin/tesseract"
        "tesseract_cmd": None,  # None = tentar detecção automática
    },

    # Limiares de confiança
    "confidence_threshold": 0.5,  # Mínimo de confiança para aceitar texto
    "low_confidence_threshold": 0.3,  # Marcar para revisão manual
}

# =============================================================================
# 4. EXTRAÇÃO DE CAMPOS DA NOTA FISCAL
# =============================================================================
"""
JUSTIFICATIVA - ESTRATÉGIA DE EXTRAÇÃO:

Para extrair campos estruturados do texto OCR, utilizamos:

1. REGEX PATTERNS:
   - Padrões específicos para cada campo (CNPJ, datas, valores)
   - Alta precisão para formatos conhecidos
   - Rápido e determinístico

2. ANÁLISE ESPACIAL:
   - Posição relativa dos campos no documento
   - Layout do DANFE é padronizado
   - Bounding boxes do OCR auxiliam localização

3. PÓS-PROCESSAMENTO:
   - Validação de CNPJ/CPF com dígitos verificadores
   - Normalização de datas e valores monetários
   - Correção de erros comuns de OCR (0/O, 1/I, etc.)

CAMPOS EXTRAÍDOS DO DANFE:
- Número da NF
- Série
- Data de emissão
- CNPJ do emitente
- Nome/Razão social do emitente
- CNPJ do destinatário
- Nome do destinatário
- Valor total
- Itens (descrição, quantidade, valor unitário, valor total)
- Chave de acesso (44 dígitos)
"""

EXTRACTION_CONFIG = {
    # Campos a extrair
    "fields": [
        "numero_nf",
        "serie",
        "data_emissao",
        "cnpj_emitente",
        "razao_social_emitente",
        "cnpj_destinatario",
        "nome_destinatario",
        "valor_total",
        "chave_acesso",
        "itens",
    ],

    # Padrões de regex para campos brasileiros
    "patterns": {
        "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
        "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
        "data": r"\d{2}/\d{2}/\d{4}",
        "valor": r"R?\$?\s*\d{1,3}(?:\.\d{3})*,\d{2}",
        "chave_acesso": r"\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}",
        "numero_nf": r"(?:N[ºo°]?\.?\s*|NF-e?\s*N[ºo°]?\.?\s*)(\d{1,9})",
        "serie": r"S[ÉE]RIE[:\s]*(\d{1,3})",
    },

    # Validações
    "validate_cnpj": True,
    "validate_cpf": True,
    "normalize_values": True,
}

# =============================================================================
# 5. CONFIGURAÇÃO DA API
# =============================================================================
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": False,
    "title": "API OCR Notas Fiscais",
    "description": "API para extração de dados de Notas Fiscais via OCR",
    "version": "1.0.0",

    # Limites
    "max_upload_size_mb": 10,
    "request_timeout": 60,  # segundos

    # CORS
    "cors_origins": ["*"],  # Ajustar em produção
}
