# 📝 Exemplo de Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto ou configure diretamente na plataforma de deploy.

## Backend (`Projeto_VC_3/.env`)

```env
# Configuração do servidor
API_HOST=0.0.0.0
API_PORT=8000
# Nota: Railway/Render usam a variável PORT automaticamente

# CORS (separar múltiplas URLs por vírgula)
CORS_ORIGINS=https://seu-app.streamlit.app,http://localhost:8501

# Debug (opcional)
DEBUG=False

# Tesseract (opcional, se necessário)
TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
```

## Frontend (`Interface/.env` ou Streamlit Cloud Secrets)

### Para Streamlit Cloud:
No painel do Streamlit Cloud, vá em **Settings** → **Secrets** e adicione:

```toml
API_BASE_URL = "https://sua-api.railway.app"
```

### Para arquivo `.env` local:
```env
API_BASE_URL=http://localhost:8000
```

## Variáveis de Ambiente por Plataforma

### Railway
- `PORT`: Definido automaticamente
- `HOST`: `0.0.0.0` (padrão)
- Configure `CORS_ORIGINS` manualmente

### Render
- `PORT`: Definido automaticamente
- `HOST`: `0.0.0.0` (padrão)
- Configure `CORS_ORIGINS` manualmente

### Streamlit Cloud
- Use **Secrets** no painel (formato TOML)
- Não use arquivo `.env` (não funciona no Streamlit Cloud)
