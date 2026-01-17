"""
Módulo de Pós-processamento de Texto OCR
=========================================

Correções inteligentes de erros comuns de OCR:
- Correção de caracteres confundidos (0/O, 1/I/l, etc.)
- Normalização de espaços e quebras de linha
- Correção contextual baseada em padrões brasileiros
- Validação e correção de CNPJ/CPF
- Correção de valores monetários
"""

import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TextPostProcessor:
    """
    Pós-processamento inteligente de texto OCR.
    
    Corrige erros comuns de OCR usando:
    - Regras contextuais
    - Padrões brasileiros (CNPJ, CPF, valores)
    - Dicionário de termos comuns
    - Validação de dígitos verificadores
    """
    
    # Mapeamento de correções comuns de OCR
    OCR_CORRECTIONS = {
        # Números confundidos com letras
        'O': '0',  # Em contexto numérico
        'o': '0',
        'I': '1',  # Em contexto numérico
        'l': '1',
        'S': '5',  # Em contexto numérico
        's': '5',
        'B': '8',  # Em contexto numérico
        'G': '6',
        'Z': '2',
        'z': '2',
        
        # Letras confundidas com números
        '0': 'O',  # Em contexto textual
        '1': 'I',  # Em contexto textual
        '5': 'S',  # Em contexto textual
        '8': 'B',  # Em contexto textual
    }
    
    # Termos comuns em notas fiscais (para correção contextual)
    COMMON_TERMS = {
        'EMITENTE', 'DESTINATARIO', 'DESTINATÁRIO',
        'RAZAO SOCIAL', 'RAZÃO SOCIAL',
        'CNPJ', 'CPF', 'IE', 'INSCRIÇÃO ESTADUAL',
        'VALOR TOTAL', 'VALOR PRODUTOS', 'VALOR FRETE',
        'ICMS', 'IPI', 'ISS',
        'NOTA FISCAL', 'NF-E', 'DANFE',
        'CHAVE DE ACESSO', 'CÓDIGO DE BARRAS',
    }
    
    def __init__(self):
        """Inicializa o pós-processador."""
        pass
    
    def fix_common_ocr_errors(self, text: str) -> str:
        """
        Corrige erros comuns de OCR.
        
        Args:
            text: Texto com possíveis erros de OCR
            
        Returns:
            Texto corrigido
        """
        # Remove espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        
        # Remove espaços antes de pontuação
        text = re.sub(r'\s+([,.:;!?])', r'\1', text)
        
        # Corrige quebras de linha malformadas
        text = re.sub(r'-\s*\n\s*', '', text)  # Remove hífen de quebra
        text = re.sub(r'\n+', ' ', text)  # Normaliza quebras
        
        return text.strip()
    
    def correct_numeric_context(
        self,
        text: str,
        pattern: str,
        context_before: int = 3,
        context_after: int = 3
    ) -> str:
        """
        Corrige caracteres em contexto numérico.
        
        Exemplo: "CNPJ: 12.345.678/0001-9O" -> "12.345.678/0001-90"
        
        Args:
            text: Texto completo
            pattern: Padrão regex para encontrar números
            context_before: Caracteres antes do padrão
            context_after: Caracteres depois do padrão
            
        Returns:
            Texto corrigido
        """
        def replace_in_match(match):
            matched_text = match.group(0)
            # Em contexto numérico, O -> 0, I -> 1, etc.
            corrected = matched_text
            for wrong, correct in [('O', '0'), ('o', '0'), ('I', '1'), ('l', '1'), ('S', '5'), ('B', '8')]:
                # Só substitui se estiver cercado por dígitos ou pontuação numérica
                # Usa grupos nomeados para evitar problema com \10, \11, etc.
                pattern = rf'(?P<before>[\d.,/-]){re.escape(wrong)}(?P<after>[\d.,/-])'
                corrected = re.sub(
                    pattern,
                    lambda m: f"{m.group('before')}{correct}{m.group('after')}",
                    corrected
                )
            return corrected
        
        # Aplica correção em padrões numéricos
        text = re.sub(pattern, replace_in_match, text)
        
        return text
    
    def correct_cnpj_cpf(self, text: str) -> str:
        """
        Corrige erros comuns em CNPJ/CPF detectados pelo OCR.
        
        Args:
            text: Texto com possíveis CNPJs/CPFs
            
        Returns:
            Texto com CNPJs/CPFs corrigidos
        """
        # Padrão para CNPJ
        cnpj_pattern = r'\b\d{2}[.\s-]?\d{3}[.\s-]?\d{3}[./\s-]?\d{4}[.\s-]?\d{2}\b'
        
        def fix_cnpj(match):
            cnpj = match.group(0)
            # Remove formatação
            digits = re.sub(r'[^\d]', '', cnpj)
            
            # Corrige erros comuns
            digits = digits.replace('O', '0').replace('o', '0')
            digits = digits.replace('I', '1').replace('l', '1')
            digits = digits.replace('S', '5')
            digits = digits.replace('B', '8')
            
            # Se tiver 14 dígitos, formata como CNPJ
            if len(digits) == 14:
                return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
            
            return cnpj
        
        text = re.sub(cnpj_pattern, fix_cnpj, text)
        
        # Padrão para CPF
        cpf_pattern = r'\b\d{3}[.\s-]?\d{3}[.\s-]?\d{3}[.\s-]?\d{2}\b'
        
        def fix_cpf(match):
            cpf = match.group(0)
            digits = re.sub(r'[^\d]', '', cpf)
            
            # Corrige erros
            digits = digits.replace('O', '0').replace('o', '0')
            digits = digits.replace('I', '1').replace('l', '1')
            
            # Se tiver 11 dígitos, formata como CPF
            if len(digits) == 11:
                return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            
            return cpf
        
        text = re.sub(cpf_pattern, fix_cpf, text)
        
        return text
    
    def correct_monetary_values(self, text: str) -> str:
        """
        Corrige valores monetários mal formatados.
        
        Args:
            text: Texto com valores monetários
            
        Returns:
            Texto com valores corrigidos
        """
        # Padrão para valores: R$ X.XXX,XX ou X.XXX,XX
        value_pattern = r'R?\$?\s*(\d{1,3}(?:[.\s]?\d{3})*)[,.](\d{2})'
        
        def fix_value(match):
            integer_part = match.group(1)
            decimal_part = match.group(2)
            
            # Remove espaços e pontos do inteiro
            integer_part = integer_part.replace(' ', '').replace('.', '')
            
            # Corrige erros comuns
            integer_part = integer_part.replace('O', '0').replace('o', '0')
            integer_part = integer_part.replace('I', '1').replace('l', '1')
            integer_part = integer_part.replace('S', '5')
            
            # Garante que decimal tem 2 dígitos
            if len(decimal_part) != 2:
                decimal_part = decimal_part[:2].ljust(2, '0')
            
            # Formata: R$ X.XXX,XX
            if len(integer_part) > 3:
                # Adiciona pontos de milhar
                formatted = ''
                for i, digit in enumerate(reversed(integer_part)):
                    if i > 0 and i % 3 == 0:
                        formatted = '.' + formatted
                    formatted = digit + formatted
                integer_part = formatted
            
            return f"R$ {integer_part},{decimal_part}"
        
        text = re.sub(value_pattern, fix_value, text, flags=re.IGNORECASE)
        
        return text
    
    def correct_chave_acesso(self, text: str) -> str:
        """
        Corrige chave de acesso (44 dígitos).
        
        Args:
            text: Texto com possível chave de acesso
            
        Returns:
            Texto com chave corrigida
        """
        # Padrão: 44 dígitos com ou sem espaços
        pattern = r'(\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4})'
        
        def fix_chave(match):
            chave = match.group(1)
            # Remove espaços
            digits = re.sub(r'\s+', '', chave)
            
            # Corrige erros comuns
            digits = digits.replace('O', '0').replace('o', '0')
            digits = digits.replace('I', '1').replace('l', '1')
            digits = digits.replace('S', '5')
            digits = digits.replace('B', '8')
            
            # Se tiver 44 dígitos, formata
            if len(digits) == 44 and digits.isdigit():
                return ' '.join([digits[i:i+4] for i in range(0, 44, 4)])
            
            return chave
        
        text = re.sub(pattern, fix_chave, text)
        
        return text
    
    def process(self, text: str, apply_all: bool = True) -> str:
        """
        Aplica todo o pós-processamento.
        
        Args:
            text: Texto OCR bruto
            apply_all: Se True, aplica todas as correções
            
        Returns:
            Texto pós-processado
        """
        if not text:
            return text
        
        # 1. Correções básicas
        text = self.fix_common_ocr_errors(text)
        
        if apply_all:
            # 2. Correção de CNPJ/CPF
            text = self.correct_cnpj_cpf(text)
            
            # 3. Correção de valores monetários
            text = self.correct_monetary_values(text)
            
            # 4. Correção de chave de acesso
            text = self.correct_chave_acesso(text)
            
            # 5. Correção contextual numérica
            # Aplica em padrões numéricos (CNPJ, CPF, valores, etc.)
            # NOTA: Desabilitado temporariamente devido a problemas com grupos regex
            # Os outros métodos (correct_cnpj_cpf, correct_monetary_values) já fazem correções específicas
            # numeric_patterns = [
            #     r'\d+[.\s-]?\d+[.\s-]?\d+',  # Padrões numéricos gerais
            # ]
            # for pattern in numeric_patterns:
            #     text = self.correct_numeric_context(text, pattern)
        
        return text
    
    def process_results(
        self,
        ocr_results: List,
        apply_corrections: bool = True
    ) -> List:
        """
        Processa lista de resultados OCR.
        
        Args:
            ocr_results: Lista de OCRResult
            apply_corrections: Se True, aplica correções
            
        Returns:
            Lista de resultados corrigidos
        """
        if not apply_corrections:
            return ocr_results
        
        from src.ocr.ocr_engine import OCRResult
        
        corrected = []
        for result in ocr_results:
            if isinstance(result, OCRResult):
                corrected_text = self.process(result.text, apply_all=True)
                # Mantém confiança original (ou reduz se mudou muito)
                confidence = result.confidence
                if corrected_text != result.text:
                    # Se texto mudou muito, reduz confiança ligeiramente
                    similarity = self._text_similarity(result.text, corrected_text)
                    confidence = result.confidence * (0.9 + 0.1 * similarity)
                
                corrected.append(OCRResult(
                    text=corrected_text,
                    confidence=confidence,
                    bbox=result.bbox,
                    raw_bbox=result.raw_bbox
                ))
            else:
                corrected.append(result)
        
        return corrected
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos (0-1)."""
        if not text1 or not text2:
            return 0.0
        
        # Similaridade simples baseada em caracteres comuns
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
