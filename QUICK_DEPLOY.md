# ⚡ Deploy Rápido - 5 Minutos

## 🎯 Opção Mais Rápida: Streamlit Cloud + Railway

### 1️⃣ Preparar Repositório GitHub

```bash
# Na raiz do projeto
git init
git add .
git commit -m "Initial commit - Ready for deploy"
git remote add origin https://github.com/SEU_USUARIO/docuextract-ai.git
git push -u origin main
```

### 2️⃣ Deploy Backend (Railway) - 2 minutos

1. Acesse: https://railway.app/
2. Faça login com GitHub
3. Clique em **"New Project"** → **"Deploy from GitHub repo"**
4. Selecione seu repositório
5. Railway detectará automaticamente o `railway.json`
6. Aguarde o build (pode levar 5-10 minutos na primeira vez)
7. **Copie a URL** gerada (ex: `https://docuextract-api.railway.app`)

### 3️⃣ Deploy Frontend (Streamlit Cloud) - 2 minutos

1. Acesse: https://share.streamlit.io/
2. Faça login com GitHub
3. Clique em **"New app"**
4. Configure:
   - **Repository**: Seu repositório
   - **Branch**: `main`
   - **Main file path**: `Interface/app_docuextract.py`
5. Clique em **"Advanced settings"**
6. Adicione em **Secrets**:
   ```toml
   API_BASE_URL = "https://sua-api.railway.app"
   ```
   (Substitua pela URL do Railway do passo 2)
7. Clique em **"Deploy"**

### 4️⃣ Atualizar CORS no Backend

No Railway, vá em **Variables** e adicione:
```
CORS_ORIGINS=https://seu-app.streamlit.app
```

(Substitua pela URL do Streamlit Cloud)

### 5️⃣ Pronto! 🎉

Acesse sua aplicação no Streamlit Cloud e teste!

---

## 🔧 Troubleshooting Rápido

**Backend não inicia?**
- Verifique logs no Railway
- Confirme que `PORT` está sendo usado (Railway define automaticamente)

**Frontend não conecta?**
- Verifique `API_BASE_URL` no Streamlit Secrets
- Teste a URL da API diretamente: `https://sua-api.railway.app/health`

**Erro de memória?**
- OCR engines são pesados
- Considere upgrade do plano Railway ($5/mês)

---

## 📚 Documentação Completa

Veja `DEPLOY_GITHUB.md` para opções avançadas e outras plataformas.
