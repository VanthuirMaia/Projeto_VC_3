# 📦 Como Instalar Tesseract OCR

## ⚡ Método Rápido (Windows - Recomendado)

Execute o script de instalação automática:

```bash
cd Projeto_VC_3
python install_tesseract.py
```

O script fará tudo automaticamente:
- ✅ Detecta se já está instalado
- 📥 Baixa o instalador
- 🚀 Abre o instalador
- ⚙️ Configura automaticamente no projeto

---

## 📋 Instalação Manual

### Windows

#### Passo 1: Baixar Instalador

Acesse: https://github.com/UB-Mannheim/tesseract/wiki

Baixe a versão mais recente:
- `tesseract-ocr-w64-setup-5.x.x.exe` (64-bit)
- `tesseract-ocr-w32-setup-5.x.x.exe` (32-bit)

#### Passo 2: Instalar

1. Execute o instalador baixado
2. **IMPORTANTE - Durante a instalação:**
   - ✅ Instale em: `C:\Program Files\Tesseract-OCR`
   - ✅ **Marque:** "Add to PATH" (adiciona ao PATH do sistema)
   - ✅ **Marque:** "Portuguese" (idioma português)

#### Passo 3: Verificar Instalação

Abra PowerShell/CMD e teste:

```bash
tesseract --version
```

Deve mostrar algo como:
```
tesseract 5.4.0
```

#### Passo 4: Configurar no Projeto

Execute o script de configuração:

```bash
python install_tesseract.py
```

Ou configure manualmente em `src/config.py`:

```python
"tesseract": {
    "lang": "por",
    "config": "--oem 3 --psm 6",
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",  # Adicione esta linha
}
```

---

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-por  # Português
```

Verifique:
```bash
tesseract --version
tesseract --list-langs  # Deve mostrar "por"
```

---

### macOS

```bash
brew install tesseract
brew install tesseract-lang  # Inclui português
```

Verifique:
```bash
tesseract --version
tesseract --list-langs
```

---

## ✅ Verificação

### Teste Rápido

Execute o script de teste:

```bash
python test_tesseract.py
```

### Teste Manual

```bash
# Verifica versão
tesseract --version

# Lista idiomas disponíveis
tesseract --list-langs

# Deve mostrar "por" (português)
```

### Teste na API

Após instalar e reiniciar a API:

```bash
python run_api.py
```

No log deve aparecer:
```
INFO:src.ocr.ocr_engine:Tesseract inicializado com sucesso (versão: 5.4.0)
INFO:src.ocr.ocr_engine:Engines OCR disponíveis: ['easyocr', 'paddleocr', 'tesseract']
```

---

## 🐛 Problemas Comuns

### Problema: "tesseract is not installed or it's not in your PATH"

**Solução:**
1. Reinstale o Tesseract
2. **Certifique-se de marcar "Add to PATH"** durante a instalação
3. Ou configure manualmente no `config.py`

### Problema: Tesseract instalado mas não encontrado

**Solução:**
1. Execute: `python install_tesseract.py`
2. O script detectará automaticamente o caminho
3. Ou configure manualmente em `config.py`

### Problema: Idioma português não encontrado

**Solução:**
1. Reinstale o Tesseract e marque "Portuguese"
2. Ou baixe manualmente: `por.traineddata`
3. Coloque em: `C:\Program Files\Tesseract-OCR\tessdata\`

### Problema: Permissão negada

**Solução (Windows):**
- Execute o instalador como Administrador
- Clique direito → "Executar como administrador"

---

## 📊 Benefícios do Tesseract

Com Tesseract instalado, você terá:

✅ **Ensemble completo:** 3 engines (EasyOCR + PaddleOCR + Tesseract)
✅ **+5-10% de precisão** em documentos complexos
✅ **Fallback confiável** se outros engines falharem
✅ **Melhor detecção** de números e códigos

---

## 🔄 Após Instalar

1. **Execute o script de configuração:**
   ```bash
   python install_tesseract.py
   ```

2. **Reinicie a API:**
   ```bash
   python run_api.py
   ```

3. **Verifique os logs:**
   ```
   Engines OCR disponíveis: ['easyocr', 'paddleocr', 'tesseract']
   ```

4. **Teste o ensemble:**
   - Acesse: http://localhost:8000/docs
   - Use `/extract` ou `/ocr`
   - Verifique `"engine_used": "ensemble"`
   - Verifique `"engines_used": ["easyocr", "paddleocr", "tesseract"]`

---

**Pronto!** O Tesseract estará integrado ao projeto. 🎉
