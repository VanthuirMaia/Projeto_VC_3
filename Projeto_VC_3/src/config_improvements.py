"""
Configurações Melhoradas para Melhor Precisão OCR
==================================================

Este arquivo contém configurações otimizadas baseadas em testes
e melhores práticas para maximizar a precisão dos modelos OCR.
"""

# =============================================================================
# CONFIGURAÇÕES DE PRÉ-PROCESSAMENTO MELHORADAS
# =============================================================================

PREPROCESSING_CONFIG_IMPROVED = {
    # Redimensionamento - aumentado para melhor qualidade
    "target_dpi": 400,  # Aumentado de 300 para 400
    "min_width": 1500,  # Aumentado de 1000
    "max_width": 5000,  # Aumentado de 4000

    # Binarização - método adaptativo melhorado
    "binarization_method": "adaptive",
    "adaptive_block_size": 15,  # Aumentado de 11 para melhor adaptação
    "adaptive_c": 3,  # Aumentado de 2

    # Remoção de ruído - mais agressiva
    "denoise": True,
    "denoise_strength": 12,  # Aumentado de 10

    # Correção de inclinação
    "deskew": True,
    "deskew_max_angle": 15,  # Aumentado de 10

    # Contraste - mais agressivo
    "enhance_contrast": True,
    "clahe_clip_limit": 3.0,  # Aumentado de 2.0
    "clahe_grid_size": (8, 8),
    
    # Novas opções
    "use_sharpening": True,
    "sharpening_sigma": 1.0,
    "sharpening_strength": 1.5,
    "use_morphology": True,
    "morphology_operation": "opening",
    "morphology_kernel_size": 2,
}

# =============================================================================
# CONFIGURAÇÕES OCR MELHORADAS
# =============================================================================

OCR_CONFIG_IMPROVED = {
    "primary_engine": "easyocr",
    
    # EasyOCR - configurações otimizadas
    "easyocr": {
        "languages": ["pt", "en"],
        "gpu": True,
        "model_storage_directory": None,
        "download_enabled": True,
        "detector": True,
        "recognizer": True,
        "verbose": False,
        "quantize": False,  # Desabilitado para melhor precisão
        "cudnn_benchmark": True,  # Acelera se GPU disponível
    },
    
    # PaddleOCR - configurações otimizadas
    "paddleocr": {
        "lang": "pt",
        "use_gpu": True,
        "use_angle_cls": True,
        "det_db_thresh": 0.25,  # Reduzido de 0.3 para detectar mais texto
        "det_db_box_thresh": 0.4,  # Reduzido de 0.5
        "det_db_unclip_ratio": 1.6,  # Aumentado para melhor detecção
        "rec_batch_num": 6,  # Processamento em batch
    },
    
    # Tesseract - configurações otimizadas
    "tesseract": {
        "lang": "por",
        # PSM 6: Assume bloco de texto uniforme (melhor para DANFE)
        # PSM 11: Texto esparso (alternativa se PSM 6 falhar)
        "config": "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/- ",
        "tesseract_cmd": None,
    },
    
    # Limiares de confiança - mais rigorosos
    "confidence_threshold": 0.4,  # Reduzido de 0.5 para capturar mais texto
    "low_confidence_threshold": 0.25,  # Reduzido de 0.3
    "high_confidence_threshold": 0.85,  # Para marcar alta confiança
    
    # Ensemble
    "ensemble_enabled": True,
    "ensemble_weights": {
        "easyocr": 0.4,
        "paddleocr": 0.4,
        "tesseract": 0.2,
    },
    "ensemble_consensus_threshold": 0.3,  # IoU mínimo para considerar mesma região
}

# =============================================================================
# CONFIGURAÇÕES DE PÓS-PROCESSAMENTO
# =============================================================================

POSTPROCESSING_CONFIG = {
    "enabled": True,
    "fix_common_errors": True,
    "correct_cnpj_cpf": True,
    "correct_monetary_values": True,
    "correct_chave_acesso": True,
    "normalize_spaces": True,
    "fix_line_breaks": True,
}

# =============================================================================
# CONFIGURAÇÕES DE EXTRAÇÃO MELHORADAS
# =============================================================================

EXTRACTION_CONFIG_IMPROVED = {
    "fields": [
        "numero_nf",
        "serie",
        "data_emissao",
        "cnpj_emitente",
        "razao_social_emitente",
        "inscricao_estadual_emitente",
        "cnpj_destinatario",
        "cpf_destinatario",
        "nome_destinatario",
        "valor_total",
        "valor_produtos",
        "valor_frete",
        "valor_icms",
        "chave_acesso",
        "itens",
    ],
    
    # Padrões melhorados (mais flexíveis)
    "patterns": {
        "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
        "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
        "data": r"\d{2}[/\-\.]\d{2}[/\-\.]\d{4}",
        "valor": r"R?\$?\s*\d{1,3}(?:\.\d{3})*[,\.]\d{2}",
        "chave_acesso": r"\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}",
        "numero_nf": r"(?:N[ºo°.]?\s*:?\s*|NF-?e?\s*:?\s*N[ºo°.]?\s*:?\s*|NUMERO\s*:?\s*)(\d{1,9})",
        "serie": r"(?:S[ÉE]RIE|SERIE)[:\s]*(\d{1,3})",
    },
    
    # Validações
    "validate_cnpj": True,
    "validate_cpf": True,
    "normalize_values": True,
    "ocr_corrections": True,
    
    # Tentativas múltiplas
    "retry_with_fuzzy": True,  # Tenta com fuzzy matching se regex falhar
    "fuzzy_threshold": 0.8,  # Similaridade mínima para fuzzy match
}
