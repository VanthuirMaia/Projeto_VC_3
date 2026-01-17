# 📘 Documentação Técnica do Projeto - Pipeline OCR para Notas Fiscais

Documento completo com explicação de métricas, parâmetros, fluxo de execução, erros superados e futuras implementações.

---

## 1. Visão Geral do Projeto

O **Pipeline OCR para Notas Fiscais** é um sistema de extração automatizada de dados de Notas Fiscais Eletrônicas (NF-e) em formato DANFE. Utiliza múltiplos engines OCR pré-treinados, pré e pós-processamento de imagens e extração estruturada via regex e validações.

### 1.1 Componentes Principais

| Módulo | Arquivo | Função |
|--------|---------|--------|
| **API** | `src/api/main.py` | Endpoints REST: `/health`, `/ocr`, `/extract` |
| **Pré-processamento** | `src/preprocessing/image_processor.py` | Pipeline básico (grayscale, resize, denoise, deskew, CLAHE) |
| **Melhorias de Imagem** | `src/preprocessing/image_enhancer.py` | Sharpening, morfologia, multi-scale, avaliação de qualidade |
| **OCR** | `src/ocr/ocr_engine.py` | Interface unificada EasyOCR, PaddleOCR, Tesseract + ensemble |
| **Pós-processamento de Texto** | `src/ocr/text_postprocessor.py` | Correção de erros OCR (CNPJ, CPF, valores, chave) |
| **Extração** | `src/extraction/nf_extractor.py` | Regex, validação CNPJ/CPF, campos estruturados |
| **Configuração** | `src/config.py` | Parâmetros centrais do pipeline |

---

## 2. Métricas

### 2.1 Métricas de Confiança

#### Confiança Geral (confidence_score)

Fórmula combinada usada na API:

```
confidence_score = (ocr_confidence_avg × 0,7) + (campos_ratio × 0,3)
```

- **ocr_confidence_avg**: Média das confianças de todos os `OCRResult` retornados pelos engines (0–1).
- **campos_ratio**: `campos_extraidos / campos_total` (ex.: 9/15 ≈ 0,6).
- **Pesos**: 70% OCR, 30% extração, para equilibrar qualidade do reconhecimento e cobertura de campos.

#### Confiança por Campo (Interface)

Ajustes em relação à base (derivada de `ocr_confidence_avg`, limitada entre 50–95%):

| Tipo de Campo | Ajuste | Motivo |
|-------------|--------|--------|
| Chave de Acesso | +12% | Regex muito específico (44 dígitos) |
| CNPJ/CPF | +10% | Validação por dígitos verificadores |
| Número NF | +8% | Padrão numérico bem definido |
| Data Emissão | +6% | Formato DD/MM/AAAA |
| Valores | +6% a +8% | Numéricos, padrão conhecido |
| Série | +5% | Numérico curto |
| Inscrição Estadual | +2% | Regex específico |
| Razão Social / Nome | -3% | Texto livre, mais variável |

#### Limiares de Confiança (OCR)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `confidence_threshold` | 0,5 | Mínimo para aceitar detecção no `filter_by_confidence` |
| `low_confidence_threshold` | 0,3 | Referência para marcar revisão manual (config_improvements) |

### 2.2 Métricas de Qualidade de Imagem (ImageEnhancer)

Retorno de `assess_image_quality()`:

| Métrica | Tipo | Descrição | Heurística |
|---------|------|-----------|------------|
| `blur_score` | float | Variância do Laplaciano | &lt; 100 → `is_blurry=True` |
| `contrast` | float | Desvio padrão dos pixels | &lt; 30 → `is_low_contrast=True` |
| `brightness` | float | Média dos pixels | &lt; 80 escuro, &gt; 200 claro |
| `noise_estimate` | float | Estimativa de ruído | Baseado em regiões não-borda |
| `is_blurry` | bool | Imagem borrada | blur_score &lt; 100 |
| `is_low_contrast` | bool | Baixo contraste | contrast &lt; 30 |
| `is_dark` | bool | Muito escura | brightness &lt; 80 |
| `is_bright` | bool | Muito clara | brightness &gt; 200 |

### 2.3 Métricas de Processamento (processing_info)

Retornadas no `/extract`:

| Campo | Descrição |
|-------|-----------|
| `pages_processed` | Número de páginas (imagem ou PDF) |
| `is_pdf` | Se o arquivo era PDF |
| `ocr_engine` | `"ensemble"` ou nome do engine |
| `engines_used` | Lista de engines utilizados |
| `total_detections` | Total de detecções antes do filtro de confiança |
| `filtered_detections` | Detecções após `filter_by_confidence` |
| `ocr_confidence_avg` | Confiança média do OCR (0–1) |

### 2.4 Campos Extraídos e Contagem

- **campos_total**: 15 (fixo em `NFData`).
- **campos_extraidos**: contagem de campos non-empty considerados em `_count_extracted_fields` (numero_nf, serie, chave_acesso, data_emissao, cnpj_emitente, razao_social_emitente, cnpj_destinatario ou cpf_destinatario, nome_destinatario, valor_total &gt; 0).

---

## 3. Parâmetros

### 3.1 Dados e Arquivos (`DATA_CONFIG` / `config.py`)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `supported_formats` | .jpg, .jpeg, .png, .pdf, .tiff, .bmp | Formatos aceitos |
| `max_file_size_mb` | 10 | Tamanho máximo por arquivo |
| `sample_images_dir` | SAMPLES_DIR | Pasta de amostras |

### 3.2 Pré-processamento (`PREPROCESSING_CONFIG`)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `target_dpi` | 300 | DPI alvo (referência para PDF e resize) |
| `min_width` | 1000 | Largura mínima (upscale se menor) |
| `max_width` | 4000 | Largura máxima (downscale se maior) |
| `binarization_method` | "adaptive" | "otsu", "adaptive" ou "sauvola" |
| `adaptive_block_size` | 11 | Tamanho do bloco no threshold adaptativo |
| `adaptive_c` | 2 | Constante subtraída da média |
| `denoise` | True | Aplicar denoising |
| `denoise_strength` | 10 | Força do fastNlMeansDenoising |
| `deskew` | True | Correção de inclinação |
| `deskew_max_angle` | 10 | Ângulo máximo de correção (graus) |
| `enhance_contrast` | True | Usar CLAHE |
| `clahe_clip_limit` | 2.0 | Limite do CLAHE |
| `clahe_grid_size` | (8, 8) | Grade do CLAHE |

### 3.3 OCR (`OCR_CONFIG`)

#### EasyOCR

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `languages` | ["pt", "en"] | Idiomas |
| `gpu` | True | Usar GPU se disponível |
| `model_storage_directory` | None | Pasta de modelos (padrão) |
| `download_enabled` | True | Baixar modelos |
| `detector` | True | Usar detector |
| `recognizer` | True | Usar reconhecedor |
| `verbose` | False | Logs |
| `quantize` | True | Quantização para menos memória |

#### PaddleOCR

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `lang` | "pt" | Idioma |
| `use_textline_orientation` | True | Classificador de orientação (substitui use_angle_cls) |
| `det_db_thresh` | 0.3 | Threshold do detector DB |
| `det_db_box_thresh` | 0.5 | Threshold de caixa |

#### Tesseract

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `lang` | "por" | Português |
| `config` | "--oem 3 --psm 6" | OEM 3 (LSTM), PSM 6 (bloco de texto) |
| `tesseract_cmd` | Caminho Windows ou None | Executável (None = detecção/PATH) |

#### Gerais

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `primary_engine` | "easyocr" | Engine padrão quando não é ensemble |
| `confidence_threshold` | 0.5 | Mínimo em `filter_by_confidence` |
| `low_confidence_threshold` | 0.3 | Referência para baixa confiança |

### 3.4 Extração (`EXTRACTION_CONFIG`)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `fields` | Lista de nomes | Campos alvo (numero_nf, serie, etc.) |
| `validate_cnpj` | True | Validar CNPJ por dígitos verificadores |
| `validate_cpf` | True | Validar CPF por dígitos verificadores |
| `normalize_values` | True | Normalizar valores monetários |

### 3.5 API (`API_CONFIG`)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `host` | 0.0.0.0 ou env | API_HOST, 0.0.0.0 padrão |
| `port` | 8000 ou env | API_PORT ou PORT |
| `max_upload_size_mb` | 10 | Tamanho máximo de upload |
| `request_timeout` | 60 | Timeout em segundos |
| `cors_origins` | ["*"] ou env | CORS_ORIGINS (split por vírgula) |
| `debug` | False ou env | DEBUG |

### 3.6 Ensemble (implementação em `ocr_engine.py`)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `engine_weights` (hardcoded) | easyocr: 0.4, paddleocr: 0.4, tesseract: 0.2 | Pesos na fusão |
| `_bbox_overlap` (IoU) | &gt; 0.3 | Considera mesma região para agrupamento |
| `consensus_bonus` | 0.1 por engine | Bônus quando vários engines concordam |

### 3.7 ImageEnhancer (parâmetros típicos)

| Função | Parâmetros principais |
|--------|------------------------|
| `unsharp_mask` | sigma=1.0, strength=1.5, threshold=0 |
| `morphological_cleanup` | operation="opening", kernel_size=2 |
| `adaptive_preprocessing` | quality_metrics (ou calculados) |
| `assess_image_quality` | — (blur &lt; 100, contrast &lt; 30, etc.) |
| `enhance_for_ocr` | use_adaptive=True, use_multiscale=False |

---

## 4. Fluxo de Execução

### 4.1 Diagrama Geral

```
┌─────────────────┐
│  Upload (File)  │
│  JPG/PNG/PDF    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────┐
│ validate_and_   │     │ ALLOWED_EXTENSIONS    │
│ load_file()     │────▶│ MAX_FILE_SIZE        │
└────────┬────────┘     └──────────────────────┘
         │
         ▼
┌─────────────────┐     PDF? ──▶ load_pdf_from_bytes / load_pdf
│ Lista de        │     Img? ──▶ PIL/numpy
│ imagens         │
└────────┬────────┘
         │
         ▼
    ┌───────────────────────────────────────────────────────────┐
    │  PARA CADA PÁGINA/IMAGEM:                                 │
    │                                                           │
    │  1. ImageProcessor.process_for_ocr(binarize=False)        │
    │     • load/resize → to_grayscale → denoise →              │
    │       enhance_contrast (CLAHE) → deskew                   │
    │                                                           │
    │  2. (Opcional) ImageEnhancer                              │
    │     • assess_image_quality()                              │
    │     • Se is_blurry ou is_low_contrast:                    │
    │       enhance_for_ocr(use_adaptive=True)                   │
    │                                                           │
    │  3. OCR                                                    │
    │     • ensemble: extract_with_ensemble → _merge_results    │
    │       → filter_by_confidence                              │
    │     • engine único: extract_text(engine) → filter_by_     │
    │       confidence                                          │
    │                                                           │
    │  4. Texto da página                                       │
    │     • ensemble: get_combined_text(use_postprocessing)     │
    │     • único: get_full_text ou get_combined_text com       │
    │       postprocessing conforme uso                         │
    └───────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ full_text =     │
│ join(páginas)   │
└────────┬────────┘
         │
         ├── /ocr ──▶ OCRResponse(text, detections, engine_used, engines_results)
         │
         └── /extract ──▶
                   │
                   ▼
             ┌─────────────────┐
             │ NFExtractor.    │
             │ extract(text)   │
             │ • _preprocess   │
             │ • regex +       │
             │   validações    │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ ocr_confidence_ │
             │ avg; campos_    │
             │ ratio;          │
             │ confidence_     │
             │ score           │
             └────────┬────────┘
                      │
                      ▼
             ExtractResponse(data=NFDataModel, raw_text?, processing_info)
```

### 4.2 Fluxo do Endpoint `/ocr`

1. `validate_and_load_file` → lista de imagens (1 para imagem, N para PDF).
2. Para cada imagem:
   - `ImageProcessor.process_for_ocr` (sem binarização).
   - Se `use_enhancements`: `ImageEnhancer.assess_image_quality`; se `is_blurry` ou `is_low_contrast`, `enhance_for_ocr(use_adaptive=True)`.
   - Se `engine in (None, "", "ensemble")`: `extract_with_ensemble` → `_merge_results` → `filter_by_confidence`; texto: `get_combined_text(use_postprocessing=use_postprocessing)`.
   - Senão: `extract_text(engine)` → `filter_by_confidence`; texto com ou sem `TextPostProcessor` conforme `use_postprocessing`.
3. Concatenação dos textos de todas as páginas → `OCRResponse`.

### 4.3 Fluxo do Endpoint `/extract`

1. Mesmo carregamento e pré-processamento por página (incluindo `ImageEnhancer` quando disponível).
2. OCR: `extract_with_ensemble` ou `extract_text(engine)`; `filter_by_confidence`; coleta de `all_ocr_confidences`.
3. Texto: `get_combined_text(use_postprocessing=True)` (ensemble) ou `get_full_text` (engine único).
4. `full_text = "\n\n".join(all_texts)`.
5. `ocr_confidence_avg = mean(all_ocr_confidences)`.
6. `NFExtractor.extract(full_text)` → `NFData`.
7. `campos_ratio = campos_extraidos / campos_total`;  
   `confidence_score = (ocr_confidence_avg * 0.7) + (campos_ratio * 0.3)`.
8. Montagem de `NFDataModel`, `processing_info` e `ExtractResponse` (com `raw_text` se `include_raw_text`).

### 4.4 Fluxo do Ensemble (`_merge_results`)

1. Coletar todos os `OCRResult` por engine com peso (easyocr 0.4, paddleocr 0.4, tesseract 0.2).
2. Score por detecção: `confidence * weight`; ordenar por score decrescente.
3. Agrupar por região: `_bbox_overlap(bbox, region_key) > 0.3`.
4. Por região:
   - 1 detecção: aceitar se texto único.
   - Várias: agrupar por texto normalizado; somar scores + `consensus_bonus`; escolher melhor; se vários engines concordam, `confidence = min(1, confidence * 1.1)`.
5. Ordenar resultado final por `(bbox[1], bbox[0])`.

### 4.5 Fluxo do NFExtractor

1. `_preprocess_text` (correções globais, se `ocr_corrections`).
2. Extração na ordem: chave_acesso, numero_nf, serie, data_emissao, CNPJs, CPF (se não houver CNPJ destinatário), valores (total, produtos, frete, ICMS), razão social emitente/destinatário, inscrição estadual.
3. `_count_extracted_fields` e `confidence_score = campos_extraidos / campos_total` (depois a API sobrescreve com a fórmula combinada).

---

## 5. Erros Encontrados e Superados

### 5.1 PaddleOCR: "Unknown argument: show_log"

- **Problema**: Parâmetro não aceito em versões recentes.
- **Solução**: Remoção de `show_log` na inicialização do PaddleOCR em `ocr_engine._init_paddleocr`.

### 5.2 PaddleOCR: "Unknown argument: use_gpu"

- **Problema**: `use_gpu` não é mais aceito; a detecção é feita internamente.
- **Solução**: Remoção de `use_gpu` na chamada do PaddleOCR.

### 5.3 PaddleOCR: "use_angle_cls" deprecado

- **Problema**: `use_angle_cls` obsoleto nas versões recentes.
- **Solução**: Uso de `use_textline_orientation` em `config.py` e em `_init_paddleocr`, com fallback para `use_angle_cls` se o primeiro não existir na assinatura.

### 5.4 PaddleOCR: "ModuleNotFoundError: No module named 'paddle'"

- **Problema**: PaddleOCR depende do `paddlepaddle`.
- **Solução**: `pip install paddlepaddle` e inclusão em `requirements.txt`.

### 5.5 Tesseract: não encontrado no sistema / PATH

- **Problema**: Tesseract não instalado ou não no PATH (especialmente no Windows).
- **Solução**:
  - `tesseract_cmd` em `config.py` (ex.: `r"C:\Program Files\Tesseract-OCR\tesseract.exe"`).
  - Configuração de `TESSDATA_PREFIX` para `tessdata` (em `_init_tesseract`).
  - Detecção automática em caminhos comuns no Windows e verificação de `por` em `get_languages`.
  - Scripts `install_tesseract.py` e documentação em `COMO_INSTALAR_TESSERACT.md`.

### 5.6 TextPostProcessor: "invalid group reference 10 at position 1"

- **Problema**: Uso de `\10`, `\11` em `re.sub` interpretados como referência de grupo.
- **Solução**: Uso de grupos nomeados `(?P<name>...)` e substituição via `m.group('before')`, `m.group('after')` em `correct_numeric_context`. O `correct_numeric_context` genérico foi desativado; correções numéricas ficam em `correct_cnpj_cpf`, `correct_monetary_values`, `correct_chave_acesso`.

### 5.7 Confiança muito baixa (~30%) na interface

- **Problema**: Uso apenas de `campos_extraidos / campos_total`, sem considerar a confiança do OCR.
- **Solução**:
  - Cálculo de `ocr_confidence_avg` a partir dos `OCRResult` filtrados.
  - `confidence_score = (ocr_confidence_avg * 0.7) + (campos_ratio * 0.3)` no `/extract`.
  - Na interface, base por campo a partir de `ocr_confidence_avg` (limitada 50–95%) e ajustes por tipo de campo (documentado em `MELHORIA_CONFIANCA.md`).

### 5.8 Diferenças entre respostas da API e da interface (Streamlit)

- **Problema**: Export/visualização não refletia todos os dados da API (raw_text, processing_info, confiança).
- **Solução**: Ajuste de `convert_api_response_to_table` e `export_to_json` para usar `processing_info` (incluindo `ocr_confidence_avg`) e incluir `raw_text`, `processing_info` e `full_data` no JSON.

### 5.9 Novo documento não atualizando na interface

- **Problema**: Ao enviar outro arquivo, a interface mantinha dados do anterior.
- **Solução**: Verificação de `is_new_file` (comparando `uploaded_file.name` com `st.session_state.current_file_name`) e limpeza de `processed_data`, `processing_info`, `raw_text`, `table_data` para forçar novo processamento.

### 5.10 Histórico com confiança diferente da Confiança Média

- **Problema**: Itens do histórico usavam apenas `confidence_score` da API.
- **Solução**: Cálculo de `avg_confidence` a partir de `st.session_state.table_data` (mesma lógica dos cards) quando disponível, com fallback para `api_data.get('confidence_score')`.

---

## 6. Futuras Implementações

### 6.1 Modelos e OCR

- **Fine-tuning** de um modelo OCR em DANFEs brasileiros para fontes e layouts específicos.
- **OCR baseado em transformers** (ex.: Donut, TrOCR) para documento completo.
- **Detecção de tabelas** e OCR específico para blocos tabulares (itens, totais).
- **Suporte a NFC-e** e outros layouts além do DANFE clássico.

### 6.2 Pré e pós-processamento

- **Segmentação de layout** (emitente, destinatário, itens, totais) antes do OCR.
- **Correção de perspectiva** automática para fotos de documentos.
- **Remoção de assinaturas/carimbos** para reduzir ruído.
- **Pós-processamento com NER** ou pequenos modelos para razão social e endereços.
- Reativação e ampliação de **correct_numeric_context** com regex seguros (grupos nomeados).

### 6.3 Extração e validação

- **Extração de itens** (código, descrição, quantidade, valores) de forma estruturada e validada.
- **Consulta à SEFAZ** (chave, status) para validar NF-e e cruzar dados.
- **Validação de Inscrição Estadual** por estado.
- **Padronização de datas** (ISO, timezone) e de unidades de medida.
- **Fuzzy matching** e **retry_with_fuzzy** (já previstos em `config_improvements`) integrados no extrator principal.

### 6.4 API e infraestrutura

- **Cache** de resultados por hash do arquivo para evitar reprocessamento.
- **Filas (Celery/RQ)** para jobs pesados e tempo de resposta assíncrono.
- **Rate limiting** e **autenticação** (JWT, API Key).
- **Métricas (Prometheus/OpenTelemetry)** e **logs estruturados**.
- **Testes de carga** e **benchmarks** de precisão por engine e por tipo de imagem.

### 6.5 Interface e integrações

- **Preview da imagem** com overlays das regiões detectadas (bbox) e confiança por bloco.
- **Modo de revisão** com sugestões de correção e feedback para melhoria de modelos.
- **Integração com ERPs** e exportação em formatos específicos (XML, CSV, planilhas).
- **API de webhooks** para notificação quando o processamento assíncrono terminar.

### 6.6 Configuração e operação

- **Painel de configuração** (limiares, pesos do ensemble, ativar/desativar engines) via API ou arquivo.
- **A/B testing** de parâmetros e de versões de modelos.
- **Documentação OpenAPI** completa e exemplos de clientes (Python, cURL, Postman).

---

## 7. Referência Rápida de Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `src/config.py` | DATA, PREPROCESSING, OCR, EXTRACTION, API |
| `src/config_improvements.py` | Variantes otimizadas e POSTPROCESSING |
| `src/api/main.py` | FastAPI, /health, /ocr, /extract |
| `src/preprocessing/image_processor.py` | Pipeline básico, PDF, deskew, CLAHE |
| `src/preprocessing/image_enhancer.py` | Qualidade, sharpening, multi-scale, adaptativo |
| `src/ocr/ocr_engine.py` | OCREngine, ensemble, _merge_results, get_combined_text |
| `src/ocr/text_postprocessor.py` | TextPostProcessor, CNPJ/CPF, valores, chave |
| `src/extraction/nf_extractor.py` | NFExtractor, NFData, regex, validações |
| `run_api.py` | Uvicorn, detecção de produção (PORT, RAILWAY_ENVIRONMENT) |

---

**Versão do documento**: 1.0  
**Última atualização**: conforme estado do repositório no momento da geração.
