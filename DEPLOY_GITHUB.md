# 🚀 Guia de Deploy via GitHub

Este guia apresenta várias opções para fazer deploy do projeto **DocuExtract AI** usando GitHub.

## 📋 Estrutura do Projeto

- **Backend**: FastAPI (`Projeto_VC_3/`)
- **Frontend**: Streamlit (`Interface/`)
- **Dependências**: OCR engines pesados (EasyOCR, PaddleOCR, Tesseract)

---

## 🎯 Opções de Deploy

### 1. **Streamlit Cloud** (Frontend) + **Railway/Render** (Backend) ⭐ Recomendado

#### **Frontend - Streamlit Cloud**

1. **Criar repositório no GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/SEU_USUARIO/docuextract-ai.git
   git push -u origin main
   ```

2. **Conectar ao Streamlit Cloud**
   - Acesse: https://share.streamlit.io/
   - Faça login com GitHub
   - Clique em "New app"
   - Selecione o repositório
   - **Main file path**: `Interface/app_docuextract.py`
   - **Branch**: `main`
   - **Python version**: `3.10` ou `3.11`

3. **Configurar variáveis de ambiente**
   - No Streamlit Cloud, vá em "Settings" → "Secrets"
   - Adicione:
   ```toml
   API_BASE_URL = "https://sua-api.railway.app"
   ```

#### **Backend - Railway** (Recomendado)

1. **Criar arquivo `railway.json`** na raiz do projeto:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "cd Projeto_VC_3 && pip install -r requirements.txt"
     },
     "deploy": {
       "startCommand": "cd Projeto_VC_3 && python run_api.py",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. **Criar `Procfile`** em `Projeto_VC_3/`:
   ```
   web: python run_api.py
   ```

3. **Criar `runtime.txt`** em `Projeto_VC_3/`:
   ```
   python-3.11.0
   ```

4. **Deploy no Railway**
   - Acesse: https://railway.app/
   - Conecte seu repositório GitHub
   - Selecione o projeto
   - Railway detectará automaticamente o `railway.json`
   - Configure variáveis de ambiente:
     - `PORT`: Railway define automaticamente
     - `HOST`: `0.0.0.0`

5. **Atualizar CORS no backend**
   - Em `Projeto_VC_3/src/config.py`, atualize:
   ```python
   "cors_origins": [
       "https://seu-app.streamlit.app",
       "http://localhost:8501"
   ]
   ```

---

### 2. **Render** (Backend + Frontend)

#### **Backend no Render**

1. **Criar `render.yaml`** na raiz:
   ```yaml
   services:
     - type: web
       name: docuextract-api
       env: python
       buildCommand: cd Projeto_VC_3 && pip install -r requirements.txt
       startCommand: cd Projeto_VC_3 && python run_api.py
       envVars:
         - key: PORT
           value: 8000
         - key: HOST
           value: 0.0.0.0
       plan: starter
   ```

2. **Deploy no Render**
   - Acesse: https://render.com/
   - Conecte repositório GitHub
   - Selecione "New Web Service"
   - Render detectará o `render.yaml`

#### **Frontend no Render**

1. **Adicionar ao `render.yaml`**:
   ```yaml
   services:
     - type: web
       name: docuextract-frontend
       env: python
       buildCommand: cd Interface && pip install -r requirements.txt
       startCommand: cd Interface && streamlit run app_docuextract.py --server.port=$PORT --server.address=0.0.0.0
       envVars:
         - key: API_BASE_URL
           value: https://docuextract-api.onrender.com
       plan: starter
   ```

---

### 3. **GitHub Actions + Docker** (Deploy Automático)

#### **Criar Dockerfiles**

**`Projeto_VC_3/Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["python", "run_api.py"]
```

**`Interface/Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app_docuextract.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### **GitHub Actions Workflow**

Criar `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        run: |
          cd Projeto_VC_3
          docker build -t docuextract-api:latest .
          # Adicione push para Docker Hub ou registry
      
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        run: |
          cd Interface
          docker build -t docuextract-frontend:latest .
```

---

## 🔧 Configurações Necessárias

### 1. **Variáveis de Ambiente**

Criar `.env.example` na raiz:
```env
# Backend
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://seu-app.streamlit.app,http://localhost:8501

# Frontend
API_BASE_URL=https://sua-api.railway.app
```

### 2. **Atualizar Configurações**

**`Projeto_VC_3/src/config.py`**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_CONFIG = {
    "title": "API OCR Notas Fiscais",
    "description": "API para extração de dados de NFs via OCR",
    "version": "1.0.0",
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", 8000)),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
}
```

**`Interface/app_docuextract.py`**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
```

### 3. **Atualizar `.gitignore`**

Adicionar na raiz:
```
.env
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
*.log
.DS_Store
```

---

## 📝 Checklist de Deploy

### Antes do Deploy

- [ ] Criar repositório no GitHub
- [ ] Adicionar `.gitignore` completo
- [ ] Criar arquivos de configuração (Dockerfile, Procfile, etc.)
- [ ] Configurar variáveis de ambiente
- [ ] Testar localmente
- [ ] Atualizar CORS no backend

### Deploy Backend

- [ ] Escolher plataforma (Railway/Render/Fly.io)
- [ ] Conectar repositório GitHub
- [ ] Configurar variáveis de ambiente
- [ ] Verificar logs de inicialização
- [ ] Testar endpoint `/health`

### Deploy Frontend

- [ ] Conectar ao Streamlit Cloud ou Render
- [ ] Configurar `API_BASE_URL`
- [ ] Testar upload de arquivo
- [ ] Verificar conexão com API

### Pós-Deploy

- [ ] Testar fluxo completo
- [ ] Verificar logs de erro
- [ ] Configurar domínio personalizado (opcional)
- [ ] Documentar URLs de produção

---

## 🐛 Troubleshooting

### Backend não inicia

- Verificar logs na plataforma
- Confirmar que `PORT` está configurado corretamente
- Verificar dependências (Tesseract pode precisar instalação manual)

### Frontend não conecta à API

- Verificar `API_BASE_URL` no Streamlit Cloud Secrets
- Confirmar CORS no backend
- Testar endpoint `/health` diretamente

### Erro de memória

- OCR engines são pesados
- Considerar upgrade de plano (Railway/Render)
- Ou usar Docker com recursos limitados

---

## 🔗 Links Úteis

- **Streamlit Cloud**: https://share.streamlit.io/
- **Railway**: https://railway.app/
- **Render**: https://render.com/
- **Fly.io**: https://fly.io/
- **GitHub Actions**: https://docs.github.com/en/actions

---

## 💡 Recomendação Final

**Para começar rápido:**
1. **Streamlit Cloud** (Frontend) - Grátis e fácil
2. **Railway** (Backend) - $5/mês, muito simples

**Para produção:**
1. **Docker** + **GitHub Actions** + **AWS/GCP**
2. Ou **Kubernetes** para escalabilidade

---

**Status**: ✅ Guia completo criado
