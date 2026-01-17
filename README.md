# Pipeline OCR para Notas Fiscais

Sistema de extração de dados de Notas Fiscais brasileiras (DANFE) utilizando OCR com modelos pré-treinados.

## Arquitetura do Pipeline

```
┌─────────────┐    ┌──────────────────┐    ┌─────────┐    ┌───────────┐    ┌──────────┐
│   Imagem    │ → │ Pré-processamento │ → │   OCR   │ → │ Extração  │ → │   JSON   │
│   (DANFE)   │    │    (OpenCV)      │    │(EasyOCR)│    │  (Regex)  │    │  (Dados) │
└─────────────┘    └──────────────────┘    └─────────┘    └───────────┘    └──────────┘
```

## Estrutura do Projeto

```
Projeto3/
├── src/
│   ├── preprocessing/     # Tratamento de imagens
│   ├── ocr/              # Engines OCR
│   ├── extraction/       # Extração de campos NF
│   ├── api/              # API REST (FastAPI)
│   └── config.py         # Configurações
├── notebooks/
│   └── pipeline_demo.ipynb
├── samples/              # Imagens de teste
├── outputs/              # Resultados
├── requirements.txt
└── run_api.py
```

## Instalação

### 1. Instalar Python e dependências

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt
```

### 2. Instalar Tesseract OCR

O projeto requer o Tesseract OCR instalado no sistema operacional.

#### Windows:
1. Baixe o instalador do Tesseract:
   - https://github.com/UB-Mannheim/tesseract/wiki
   - Recomendado: `tesseract-ocr-w64-setup-5.x.x.exe`
2. Execute o instalador e instale no caminho padrão: `C:\Program Files\Tesseract-OCR`
3. (Opcional) Adicione ao PATH do sistema, ou configure manualmente em `src/config.py`:
   ```python
   "tesseract": {
       "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
       ...
   }
   ```
4. Baixe o pacote de idioma português durante a instalação, ou baixe separadamente:
   - https://github.com/tesseract-ocr/tessdata

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-por  # Português
```

#### Linux (Fedora/RHEL):
```bash
sudo dnf install tesseract
sudo dnf install tesseract-langpack-por  # Português
```

#### macOS:
```bash
brew install tesseract
brew install tesseract-lang  # Inclui português
```

### 3. Verificar Instalação

Após instalar, teste o Tesseract:

```bash
# Verificar versão
tesseract --version

# Testar OCR
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

**Nota:** O código detecta automaticamente o Tesseract no Windows. Se não encontrar, configure manualmente em `src/config.py`.

## Uso

### Via API REST

```bash
# Iniciar servidor
python run_api.py

# Acessar documentação
# http://localhost:8000/docs
```

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Status da API |
| POST | `/ocr` | Apenas OCR (texto bruto) |
| POST | `/extract` | Extração completa de dados |

**Exemplo com curl:**

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@nota_fiscal.jpg"
```

**Exemplo com Python:**

```python
import requests

with open('nota_fiscal.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/extract',
        files={'file': f}
    )

data = response.json()
print(data['data']['cnpj_emitente'])
print(data['data']['valor_total'])
```

### Via Código Python

```python
from src.preprocessing import ImageProcessor
from src.ocr import OCREngine
from src.extraction import NFExtractor

# Pipeline
processor = ImageProcessor()
ocr = OCREngine()
extractor = NFExtractor()

# Processar imagem
image = processor.process_for_ocr('nota_fiscal.jpg')
results = ocr.extract_text(image, detail=True)
text = ocr.get_full_text(results)

# Extrair dados
nf_data = extractor.extract(text)
print(nf_data.to_dict())
```

---

## Justificativas Técnicas

### 1. Base de Dados

**Escolha:** Modelos OCR pré-treinados (sem dataset próprio)

**Justificativa:**
- EasyOCR e PaddleOCR foram treinados em milhões de imagens
- Suporte nativo a português brasileiro
- O desafio está na extração estruturada, não no reconhecimento
- Fine-tuning seria necessário apenas para fontes muito específicas

### 2. Técnicas de Tratamento de Imagens

| Técnica | Justificativa |
|---------|---------------|
| **Escala de Cinza** | Reduz complexidade, remove cor irrelevante para texto |
| **Redimensionamento** | Mínimo 300 DPI para boa leitura |
| **Binarização Adaptativa** | Separa texto do fundo em iluminação irregular |
| **Remoção de Ruído** | Elimina artefatos de digitalização |
| **Correção de Inclinação** | Documentos tortos reduzem precisão do OCR |
| **CLAHE** | Melhora contraste em documentos desbotados |

### 3. Modelos OCR

**Modelo Principal: EasyOCR**

| Aspecto | Detalhe |
|---------|---------|
| Arquitetura | CRAFT (detector) + CRNN (reconhecedor) |
| Precisão | 95-98% em texto impresso |
| Idiomas | Suporte a 80+ idiomas incluindo PT-BR |
| GPU | Aceleração disponível |

**Por que EasyOCR:**
- Deep Learning com CNN + BiLSTM
- Detecta texto em diferentes orientações
- Retorna bounding boxes precisos
- Bom desempenho em fontes pequenas (comum em NFs)

**Alternativas implementadas:**
- **PaddleOCR:** Estado da arte, rápido, bom para tabelas
- **Tesseract:** Fallback confiável, mantido pelo Google, requer instalação separada

### 4. Extração de Campos

**Estratégia:** Regex patterns + Validação

**Campos extraídos do DANFE:**
- Número da NF e Série
- Chave de Acesso (44 dígitos)
- Data de Emissão
- CNPJ/CPF do Emitente e Destinatário
- Razão Social / Nome
- Valores (total, produtos, frete, ICMS)

**Validações:**
- CNPJ: Algoritmo de dígitos verificadores
- CPF: Algoritmo de dígitos verificadores
- Chave de Acesso: 44 dígitos numéricos

---

## Resposta da API

```json
{
  "success": true,
  "data": {
    "numero_nf": "123456",
    "serie": "1",
    "chave_acesso": "35240612345678901234560001000100001234567890",
    "data_emissao": "15/01/2024",
    "cnpj_emitente": "12.345.678/0001-90",
    "razao_social_emitente": "EMPRESA EXEMPLO LTDA",
    "cnpj_destinatario": "98.765.432/0001-10",
    "nome_destinatario": "CLIENTE TESTE S/A",
    "valor_total": 1284.56,
    "confidence_score": 0.85,
    "campos_extraidos": 9
  },
  "processing_info": {
    "ocr_engine": "easyocr",
    "total_detections": 45
  }
}
```

## Tecnologias

- **Python 3.10+**
- **OpenCV** - Processamento de imagens
- **EasyOCR** - OCR principal
- **PaddleOCR** - OCR alternativo
- **FastAPI** - API REST
- **Pydantic** - Validação de dados

## Licença

MIT
