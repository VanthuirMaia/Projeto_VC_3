"""
Módulo de Melhorias Avançadas de Pré-processamento
==================================================

Técnicas adicionais para melhorar a qualidade das imagens antes do OCR:
- Sharpening (nitidez)
- Morphological operations avançadas
- Multi-scale processing
- Quality assessment
- Adaptive preprocessing
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """
    Melhorias avançadas de pré-processamento para OCR.
    
    Técnicas implementadas:
    - Unsharp masking (aumento de nitidez)
    - Morphological operations (dilatação/erosão)
    - Multi-scale enhancement
    - Quality assessment
    - Adaptive thresholding melhorado
    """

    def __init__(self):
        """Inicializa o enhancer."""
        pass

    def unsharp_mask(
        self,
        image: np.ndarray,
        sigma: float = 1.0,
        strength: float = 1.5,
        threshold: int = 0
    ) -> np.ndarray:
        """
        Aplica unsharp masking para aumentar nitidez.
        
        Justificativa: Texto borrado reduz precisão do OCR.
        Unsharp masking realça bordas e melhora legibilidade.
        
        Args:
            image: Imagem em grayscale
            sigma: Desvio padrão do blur gaussiano
            strength: Força do sharpening (1.0 = sem efeito)
            threshold: Limiar mínimo de diferença para aplicar
            
        Returns:
            Imagem com nitidez aumentada
        """
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplica blur gaussiano
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        
        # Calcula diferença
        diff = image.astype(np.float32) - blurred.astype(np.float32)
        
        # Aplica threshold
        if threshold > 0:
            mask = np.abs(diff) > threshold
            diff = diff * mask
        
        # Aplica sharpening
        sharpened = image.astype(np.float32) + strength * diff
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return sharpened

    def morphological_cleanup(
        self,
        image: np.ndarray,
        operation: str = "opening",
        kernel_size: int = 2
    ) -> np.ndarray:
        """
        Aplica operações morfológicas para limpar imagem.
        
        Justificativa: Remove ruído pontual e conecta caracteres
        quebrados, melhorando detecção de texto.
        
        Args:
            image: Imagem binária
            operation: "opening", "closing", "gradient", "tophat", "blackhat"
            kernel_size: Tamanho do kernel estruturante
            
        Returns:
            Imagem processada
        """
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Cria kernel estruturante
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (kernel_size, kernel_size)
        )
        
        if operation == "opening":
            # Remove ruído pequeno
            result = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        elif operation == "closing":
            # Conecta caracteres próximos
            result = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        elif operation == "gradient":
            # Detecta bordas
            result = cv2.morphologyEx(image, cv2.MORPH_GRADIENT, kernel)
        elif operation == "tophat":
            # Destaque de elementos claros
            result = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
        elif operation == "blackhat":
            # Destaque de elementos escuros
            result = cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel)
        else:
            result = image
        
        return result

    def adaptive_threshold_improved(
        self,
        image: np.ndarray,
        method: str = "gaussian",
        block_size: int = 11,
        c: int = 2,
        use_otsu: bool = False
    ) -> np.ndarray:
        """
        Binarização adaptativa melhorada com múltiplas estratégias.
        
        Justificativa: Combina métodos para melhor separação
        texto/fundo em diferentes condições de iluminação.
        
        Args:
            image: Imagem em grayscale
            method: "gaussian" ou "mean"
            block_size: Tamanho da região local (deve ser ímpar)
            c: Constante subtraída da média
            use_otsu: Se True, usa Otsu como fallback
            
        Returns:
            Imagem binária
        """
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Garante block_size ímpar
        if block_size % 2 == 0:
            block_size += 1
        
        # Aplica threshold adaptativo
        if method == "gaussian":
            binary = cv2.adaptiveThreshold(
                image, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                block_size, c
            )
        else:  # mean
            binary = cv2.adaptiveThreshold(
                image, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                block_size, c
            )
        
        # Se Otsu habilitado e resultado parece ruim, tenta Otsu
        if use_otsu:
            # Calcula métrica de qualidade (razão de pixels brancos)
            white_ratio = np.sum(binary == 255) / binary.size
            if white_ratio < 0.1 or white_ratio > 0.9:
                # Muito preto ou muito branco - tenta Otsu
                _, otsu_binary = cv2.threshold(
                    image, 0, 255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                return otsu_binary
        
        return binary

    def multi_scale_enhancement(
        self,
        image: np.ndarray,
        scales: list = [1.0, 1.5, 2.0]
    ) -> np.ndarray:
        """
        Processa imagem em múltiplas escalas e combina resultados.
        
        Justificativa: Diferentes escalas capturam diferentes
        níveis de detalhe. Combinação melhora precisão geral.
        
        Args:
            image: Imagem original
            scales: Lista de fatores de escala
            
        Returns:
            Imagem melhorada
        """
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        enhanced_images = []
        
        for scale in scales:
            # Redimensiona
            if scale != 1.0:
                h, w = image.shape[:2]
                new_h, new_w = int(h * scale), int(w * scale)
                scaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            else:
                scaled = image.copy()
            
            # Aplica sharpening
            sharpened = self.unsharp_mask(scaled, sigma=1.0, strength=1.2)
            
            # Volta para escala original se necessário
            if scale != 1.0:
                h, w = image.shape[:2]
                sharpened = cv2.resize(sharpened, (w, h), interpolation=cv2.INTER_AREA)
            
            enhanced_images.append(sharpened)
        
        # Combina usando média ponderada (escala original tem mais peso)
        weights = [0.5, 0.3, 0.2]  # Pesos para cada escala
        combined = np.zeros_like(image, dtype=np.float32)
        
        for img, weight in zip(enhanced_images, weights):
            combined += img.astype(np.float32) * weight
        
        return np.clip(combined, 0, 255).astype(np.uint8)

    def assess_image_quality(self, image: np.ndarray) -> dict:
        """
        Avalia qualidade da imagem para ajuste adaptativo.
        
        Métricas:
        - Blur (nível de borrão)
        - Contraste
        - Brilho médio
        - Ruído estimado
        
        Args:
            image: Imagem para avaliar
            
        Returns:
            Dicionário com métricas de qualidade
        """
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Blur: variância do Laplaciano
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        blur_score = laplacian.var()
        
        # Contraste: desvio padrão
        contrast = image.std()
        
        # Brilho médio
        brightness = image.mean()
        
        # Ruído estimado: variância em região uniforme
        # Usa bordas para estimar ruído
        edges = cv2.Canny(image, 50, 150)
        noise_estimate = image[edges == 0].std() if np.any(edges == 0) else 0
        
        return {
            "blur_score": float(blur_score),
            "contrast": float(contrast),
            "brightness": float(brightness),
            "noise_estimate": float(noise_estimate),
            "is_blurry": blur_score < 100,  # Threshold empírico
            "is_low_contrast": contrast < 30,
            "is_dark": brightness < 80,
            "is_bright": brightness > 200,
        }

    def adaptive_preprocessing(
        self,
        image: np.ndarray,
        quality_metrics: dict = None
    ) -> np.ndarray:
        """
        Aplica pré-processamento adaptativo baseado em qualidade.
        
        Justificativa: Diferentes imagens precisam de diferentes
        tratamentos. Análise de qualidade permite otimização.
        
        Args:
            image: Imagem original
            quality_metrics: Métricas de qualidade (calcula se None)
            
        Returns:
            Imagem processada adaptativamente
        """
        if quality_metrics is None:
            quality_metrics = self.assess_image_quality(image)
        
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        processed = image.copy()
        
        # Se muito borrado, aplica sharpening agressivo
        if quality_metrics["is_blurry"]:
            processed = self.unsharp_mask(processed, sigma=1.5, strength=2.0)
            logger.info("Aplicado sharpening agressivo (imagem borrada)")
        
        # Se baixo contraste, aplica CLAHE
        if quality_metrics["is_low_contrast"]:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            processed = clahe.apply(processed)
            logger.info("Aplicado CLAHE (baixo contraste)")
        
        # Se muito escuro, aumenta brilho
        if quality_metrics["is_dark"]:
            processed = cv2.convertScaleAbs(processed, alpha=1.2, beta=20)
            logger.info("Aumentado brilho (imagem escura)")
        
        # Se muito claro, reduz brilho
        if quality_metrics["is_bright"]:
            processed = cv2.convertScaleAbs(processed, alpha=0.9, beta=-10)
            logger.info("Reduzido brilho (imagem clara)")
        
        return processed

    def enhance_for_ocr(
        self,
        image: np.ndarray,
        use_adaptive: bool = True,
        use_multiscale: bool = False
    ) -> np.ndarray:
        """
        Pipeline completo de melhorias para OCR.
        
        Args:
            image: Imagem original
            use_adaptive: Se True, usa processamento adaptativo
            use_multiscale: Se True, usa multi-scale enhancement
            
        Returns:
            Imagem otimizada para OCR
        """
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        if use_multiscale:
            processed = self.multi_scale_enhancement(image)
        elif use_adaptive:
            quality = self.assess_image_quality(image)
            processed = self.adaptive_preprocessing(image, quality)
        else:
            # Processamento padrão
            processed = self.unsharp_mask(image, sigma=1.0, strength=1.3)
        
        return processed
