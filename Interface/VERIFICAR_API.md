# 🔧 Como Verificar e Iniciar a API

## ❌ Erro: "Não foi possível conectar à API"

Este erro significa que a API FastAPI não está rodando. Siga os passos abaixo para resolver.

---

## ✅ Solução: Iniciar a API

### Passo 1: Verificar se Python está instalado

```bash
python --version
```

Deve mostrar: `Python 3.8` ou superior.

---

### Passo 2: Navegar até a pasta da API

```bash
cd "API\Projeto_VC_3"
```

**Caminho completo no Windows:**
```
C:\Users\Rodri\Desktop\atividade-visao-computacinal\Atividade 3\API\Projeto_VC_3
```

---

### Passo 3: Instalar dependências (se ainda não instalou)

```bash
pip install -r requirements.txt
```

**Nota:** A primeira instalação pode demorar (EasyOCR baixa modelos grandes).

---

### Passo 4: Iniciar a API

```bash
python run_api.py
```

Você deve ver:
```
============================================================
API OCR Notas Fiscais
============================================================
Iniciando servidor em http://localhost:8000
Documentação: http://localhost:8000/docs
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### Passo 5: Verificar se a API está funcionando

Abra seu navegador e acesse:

- **Health Check:** http://localhost:8000/health
- **Documentação Swagger:** http://localhost:8000/docs

Você deve ver uma resposta JSON como:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ocr_engines": ["easyocr", ...]
}
```

---

### Passo 6: Voltar ao Streamlit

1. **Não feche o terminal** onde a API está rodando
2. No Streamlit, clique em **🔄 Recarregar** ou pressione **R**
3. O aviso deve desaparecer e mostrar: **✅ API conectada**

---

## 🐛 Problemas Comuns

### ❌ Erro: "ModuleNotFoundError: No module named 'uvicorn'"

**Solução:**
```bash
pip install uvicorn fastapi
```

Ou instale todas as dependências:
```bash
pip install -r requirements.txt
```

---

### ❌ Erro: "Address already in use" ou porta 8000 ocupada

**Solução 1:** Encontre o processo usando a porta 8000 e encerre-o:
```bash
# Windows PowerShell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**Solução 2:** Altere a porta da API em `API/Projeto_VC_3/src/config.py`:
```python
API_CONFIG = {
    "port": 8001,  # Mude para 8001 ou outra porta
    ...
}
```

E atualize `Interface/app_docuextract.py`:
```python
API_BASE_URL = "http://localhost:8001"  # Mesma porta
```

---

### ❌ Erro: "EasyOCR não instalado"

**Solução:**
```bash
pip install easyocr
```

**Nota:** A primeira execução baixa modelos (~500MB). Aguarde.

---

### ❌ Erro: "No module named 'src'"

**Solução:** Execute de dentro da pasta `API/Projeto_VC_3`:
```bash
cd "API\Projeto_VC_3"
python run_api.py
```

---

## 📋 Checklist

- [ ] Python 3.8+ instalado
- [ ] Navegou até `API\Projeto_VC_3`
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] API iniciada (`python run_api.py`)
- [ ] Terminal mostra: `Uvicorn running on http://0.0.0.0:8000`
- [ ] Teste em navegador: http://localhost:8000/health funciona
- [ ] Streamlit mostra: **✅ API conectada**

---

## 🎯 Teste Rápido

### Terminal 1 (API):
```bash
cd "API\Projeto_VC_3"
python run_api.py
```

### Terminal 2 (Streamlit):
```bash
cd Interface
streamlit run app_docuextract.py
```

### Navegador:
1. Streamlit: http://localhost:8501
2. API Health: http://localhost:8000/health
3. API Docs: http://localhost:8000/docs

---

## 💡 Dica

Mantenha **dois terminais abertos**:
- **Terminal 1:** API rodando (`python run_api.py`)
- **Terminal 2:** Streamlit rodando (`streamlit run app_docuextract.py`)

Se fechar a API, o Streamlit não conseguirá processar arquivos.

---

**Ainda com problemas?** Verifique os logs no terminal da API para mais detalhes.
