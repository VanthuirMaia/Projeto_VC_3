"""
Módulo de Pré-processamento de Imagens para OCR
================================================

Este módulo implementa técnicas de tratamento de imagens
otimizadas para melhorar a precisão do OCR em documentos.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union, List
from PIL import Image
import io

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class ImageProcessor:
    """
    Processador de imagens para preparação de documentos para OCR.

    Técnicas implementadas:
    - Conversão para escala de cinza
    - Redimensionamento adaptativo
    - Binarização (Otsu, Adaptativo, Sauvola)
    - Remoção de ruído
    - Correção de inclinação (deskew)
    - Aumento de contraste (CLAHE)
    """

    def __init__(self, config: dict = None):
        """
        Inicializa o processador com configurações.

        Args:
            config: Dicionário de configurações de pré-processamento
        """
        self.config = config or self._default_config()

    def _default_config(self) -> dict:
        """Retorna configurações padrão."""
        return {
            "target_dpi": 300,
            "min_width": 1000,
            "max_width": 4000,
            "binarization_method": "adaptive",
            "adaptive_block_size": 11,
            "adaptive_c": 2,
            "denoise": True,
            "denoise_strength": 10,
            "deskew": True,
            "deskew_max_angle": 10,
            "enhance_contrast": True,
            "clahe_clip_limit": 2.0,
            "clahe_grid_size": (8, 8),
        }

    def load_image(self, source: Union[str, Path, bytes, np.ndarray]) -> np.ndarray:
        """
        Carrega imagem de diferentes fontes (incluindo PDF).

        Args:
            source: Caminho do arquivo, bytes ou array numpy

        Returns:
            Imagem como array numpy (BGR)
        """
        if isinstance(source, np.ndarray):
            return source

        if isinstance(source, bytes):
            # Verifica se é PDF pelos magic bytes
            if source[:4] == b'%PDF':
                images = self.load_pdf_from_bytes(source)
                return images[0] if images else None
            nparr = np.frombuffer(source, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {path}")

            # Verifica se é PDF
            if path.suffix.lower() == '.pdf':
                images = self.load_pdf(path)
                return images[0] if images else None

            return cv2.imread(str(path))

        raise ValueError(f"Tipo de fonte não suportado: {type(source)}")

    def load_pdf(self, pdf_path: Union[str, Path], dpi: int = 300) -> List[np.ndarray]:
        """
        Carrega PDF e converte cada página em imagem.

        Args:
            pdf_path: Caminho do arquivo PDF
            dpi: Resolução de renderização (padrão 300 DPI)

        Returns:
            Lista de imagens (uma por página)
        """
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF não instalado. Use: pip install PyMuPDF")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        images = []
        doc = fitz.open(str(pdf_path))

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Matriz de zoom para alcançar DPI desejado (72 é o DPI padrão do PDF)
                zoom = dpi / 72
                matrix = fitz.Matrix(zoom, zoom)

                # Renderiza página como imagem
                pix = page.get_pixmap(matrix=matrix)

                # Converte para numpy array
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n
                )

                # Converte RGB para BGR (OpenCV)
                if pix.n == 4:  # RGBA
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:  # RGB
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                images.append(img)
        finally:
            doc.close()

        return images

    def load_pdf_from_bytes(self, pdf_bytes: bytes, dpi: int = 300) -> List[np.ndarray]:
        """
        Carrega PDF de bytes e converte em imagens.

        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            dpi: Resolução de renderização

        Returns:
            Lista de imagens
        """
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF não instalado. Use: pip install PyMuPDF")

        images = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                zoom = dpi / 72
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix)

                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n
                )

                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                images.append(img)
        finally:
            doc.close()

        return images

    def process_pdf(
        self,
        pdf_source: Union[str, Path, bytes],
        dpi: int = 300,
        binarize: bool = False
    ) -> List[np.ndarray]:
        """
        Processa todas as páginas de um PDF para OCR.

        Args:
            pdf_source: Caminho ou bytes do PDF
            dpi: Resolução de renderização
            binarize: Se deve binarizar as imagens

        Returns:
            Lista de imagens processadas
        """
        if isinstance(pdf_source, bytes):
            images = self.load_pdf_from_bytes(pdf_source, dpi)
        else:
            images = self.load_pdf(pdf_source, dpi)

        processed = []
        for img in images:
            proc_img = self.process_for_ocr(img, binarize=binarize)
            processed.append(proc_img)

        return processed

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Converte imagem para escala de cinza.

        Justificativa: Reduz complexidade e remove informação
        de cor irrelevante para reconhecimento de texto.
        """
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Redimensiona imagem para tamanho adequado ao OCR.

        Justificativa: Imagens muito pequenas têm baixa precisão,
        imagens muito grandes consomem memória desnecessária.
        """
        height, width = image.shape[:2]

        # Calcula novo tamanho mantendo proporção
        if width < self.config["min_width"]:
            scale = self.config["min_width"] / width
        elif width > self.config["max_width"]:
            scale = self.config["max_width"] / width
        else:
            return image

        new_width = int(width * scale)
        new_height = int(height * scale)

        # Interpolação de alta qualidade
        interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
        return cv2.resize(image, (new_width, new_height), interpolation=interpolation)

    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove ruído da imagem.

        Justificativa: Artefatos de digitalização prejudicam
        a detecção e reconhecimento de caracteres.
        """
        if not self.config["denoise"]:
            return image

        strength = self.config["denoise_strength"]

        if len(image.shape) == 2:  # Grayscale
            return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
        else:  # Color
            return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Melhora contraste usando CLAHE.

        Justificativa: Contrast Limited Adaptive Histogram Equalization
        melhora legibilidade de documentos com iluminação irregular
        ou texto desbotado, preservando detalhes locais.
        """
        if not self.config["enhance_contrast"]:
            return image

        # Converte para grayscale se necessário
        if len(image.shape) == 3:
            image = self.to_grayscale(image)

        clahe = cv2.createCLAHE(
            clipLimit=self.config["clahe_clip_limit"],
            tileGridSize=self.config["clahe_grid_size"]
        )
        return clahe.apply(image)

    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Binariza a imagem (converte para preto e branco).

        Justificativa: Separa texto do fundo de forma clara,
        facilitando a detecção de caracteres pelo OCR.
        """
        # Garante que a imagem está em grayscale
        if len(image.shape) == 3:
            image = self.to_grayscale(image)

        method = self.config["binarization_method"]

        if method == "otsu":
            # Otsu's method - bom para documentos com iluminação uniforme
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        elif method == "adaptive":
            # Adaptive threshold - bom para iluminação irregular
            binary = cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.config["adaptive_block_size"],
                self.config["adaptive_c"]
            )

        elif method == "sauvola":
            # Sauvola - especializado para documentos
            binary = self._sauvola_threshold(image)

        else:
            raise ValueError(f"Método de binarização desconhecido: {method}")

        return binary

    def _sauvola_threshold(self, image: np.ndarray, window_size: int = 25, k: float = 0.5) -> np.ndarray:
        """
        Implementa binarização de Sauvola.

        Especialmente eficaz para documentos com variação
        de iluminação e texto fino.
        """
        # Calcula média e desvio padrão locais
        mean = cv2.blur(image.astype(np.float64), (window_size, window_size))
        mean_sq = cv2.blur(image.astype(np.float64) ** 2, (window_size, window_size))
        std = np.sqrt(np.maximum(mean_sq - mean ** 2, 0))

        # Calcula limiar
        R = 128  # Valor dinâmico máximo do desvio padrão
        threshold = mean * (1 + k * (std / R - 1))

        # Aplica limiar
        binary = np.zeros_like(image)
        binary[image > threshold] = 255

        return binary.astype(np.uint8)

    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige inclinação do documento.

        Justificativa: Documentos escaneados frequentemente ficam
        levemente inclinados, o que prejudica significativamente
        a precisão do OCR.
        """
        if not self.config["deskew"]:
            return image

        # Garante imagem binária para detecção de ângulo
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image.copy()

        # Inverte se necessário (texto deve ser branco)
        if np.mean(gray) > 127:
            gray = 255 - gray

        # Detecta ângulo usando Hough Transform
        angle = self._detect_skew_angle(gray)

        # Limita correção ao máximo configurado
        max_angle = self.config["deskew_max_angle"]
        if abs(angle) > max_angle:
            return image

        # Aplica rotação
        if abs(angle) > 0.1:  # Só corrige se > 0.1 graus
            return self._rotate_image(image, angle)

        return image

    def _detect_skew_angle(self, image: np.ndarray) -> float:
        """Detecta ângulo de inclinação usando projeção horizontal."""
        # Detecta bordas
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Hough Transform para detectar linhas
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, 100,
            minLineLength=100, maxLineGap=10
        )

        if lines is None or len(lines) == 0:
            return 0.0

        # Calcula ângulos das linhas detectadas
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Evita divisão por zero
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                # Considera apenas linhas aproximadamente horizontais
                if abs(angle) < 45:
                    angles.append(angle)

        if not angles:
            return 0.0

        # Retorna mediana dos ângulos
        return np.median(angles)

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotaciona imagem pelo ângulo especificado."""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)

        # Matriz de rotação
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calcula novo tamanho para não cortar a imagem
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))

        # Ajusta translação
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]

        # Aplica rotação
        border_color = 255 if len(image.shape) == 2 else (255, 255, 255)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (new_width, new_height),
            borderMode=cv2.BORDER_CONSTANT, borderValue=border_color
        )

        return rotated

    def process(
        self,
        image: Union[str, Path, bytes, np.ndarray],
        return_steps: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, dict]]:
        """
        Executa pipeline completo de pré-processamento.

        Args:
            image: Imagem de entrada (caminho, bytes ou array)
            return_steps: Se True, retorna também imagens intermediárias

        Returns:
            Imagem processada (e opcionalmente dict com etapas)
        """
        steps = {}

        # 1. Carrega imagem
        img = self.load_image(image)
        steps["original"] = img.copy()

        # 2. Redimensiona
        img = self.resize_image(img)
        steps["resized"] = img.copy()

        # 3. Converte para grayscale
        img = self.to_grayscale(img)
        steps["grayscale"] = img.copy()

        # 4. Remove ruído
        img = self.denoise(img)
        steps["denoised"] = img.copy()

        # 5. Melhora contraste
        img = self.enhance_contrast(img)
        steps["contrast_enhanced"] = img.copy()

        # 6. Corrige inclinação
        img = self.deskew(img)
        steps["deskewed"] = img.copy()

        # 7. Binariza (opcional - alguns OCRs preferem grayscale)
        # A binarização é mantida como método separado
        # para flexibilidade

        if return_steps:
            return img, steps
        return img

    def process_for_ocr(
        self,
        image: Union[str, Path, bytes, np.ndarray],
        binarize: bool = False
    ) -> np.ndarray:
        """
        Processa imagem especificamente para OCR.

        Args:
            image: Imagem de entrada
            binarize: Se True, aplica binarização final

        Returns:
            Imagem pronta para OCR
        """
        img = self.process(image, return_steps=False)

        if binarize:
            img = self.binarize(img)

        return img
