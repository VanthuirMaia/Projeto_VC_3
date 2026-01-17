# 🚀 Como Executar o DocuExtract AI (Streamlit)

## ⚡ Execução Rápida (2 Passos)

### 1️⃣ Iniciar a API Backend

Abra um terminal e execute:

```bash
cd "API\Projeto_VC_3"
python run_api.py
```

✅ A API estará rodando em: **http://localhost:8000**

---

### 2️⃣ Iniciar o Frontend Streamlit

Abra **outro terminal** e execute:

```bash
cd Interface
streamlit run app_docuextract.py
```

✅ O frontend abrirá automaticamente em: **http://localhost:8501**

---

## 📋 Pré-requisitos

1. ✅ **Python 3.8+** instalado
2. ✅ Dependências instaladas: `pip install -r requirements.txt`

---

## 🔧 Instalação de Dependências

### Backend (API)

```bash
cd "API\Projeto_VC_3"
pip install -r requirements.txt
```

### Frontend (Streamlit)

```bash
cd Interface
pip install -r requirements.txt
```

Isso instala:
- Streamlit
- Requests (para chamadas à API)
- Pandas (para manipulação de dados)
- Pillow e NumPy

---

## 🧪 Testar a Aplicação

1. **Verificar API**: Acesse http://localhost:8000/health no navegador
2. **Abrir Frontend**: http://localhost:8501 (abre automaticamente)
3. **Fazer Upload**: Arraste ou selecione uma nota fiscal (PNG, JPG, PDF)
4. **Aguardar Processamento**: A API extrairá os dados (pode levar alguns segundos)
5. **Revisar Dados**: Edite os campos extraídos na tabela se necessário
6. **Exportar**: Clique nos botões JSON, CSV ou Markdown para baixar

---

## 🎯 Funcionalidades

✅ **Upload de Arquivos**
- Suporte para PDF, PNG, JPG até 200MB
- Interface drag-and-drop

✅ **Extração de Dados**
- Integração com API FastAPI
- Extração automática de campos da NF
- Barra de progresso durante processamento

✅ **Revisão e Edição**
- Tabela editável com todos os campos
- Adicionar/remover campos
- Ajustar valores extraídos

✅ **Estatísticas**
- Total de campos extraídos
- Confiança média da extração
- Status do processamento

✅ **Exportação**
- Exportar para JSON
- Exportar para CSV (Excel)
- Exportar para Markdown

✅ **Histórico**
- Lista de documentos processados
- Estatísticas agregadas
- Revisão de documentos anteriores

---

## 🐛 Solução de Problemas

### ❌ Erro: "Cannot connect to API"

**Solução:** 
1. Verifique se a API está rodando: http://localhost:8000/health
2. Confirme que a URL da API está correta no código: `API_BASE_URL = "http://localhost:8000"`

### ❌ Erro: "Module not found: requests" ou "Module not found: pandas"

**Solução:**
```bash
pip install requests pandas
```

### ❌ Erro: "Porta 8501 já em uso"

**Solução:** Streamlit tentará usar outra porta automaticamente. Verifique o terminal para o novo endereço.

### ❌ Erro: "EasyOCR não encontrado"

**Solução:** A primeira execução da API baixa modelos grandes. Aguarde o download.

---

## 📁 Arquivos

- **`app_docuextract.py`**: Aplicação Streamlit principal (equivalente ao React)
- **`requirements.txt`**: Dependências Python
- **`app.py`**: Aplicação antiga (Veritas ArtLab - análise de arte)

---

## 🎨 Comparação com React

O arquivo `app_docuextract.py` replica todas as funcionalidades do componente React `streamlit-preview.tsx`:

| Funcionalidade | React | Streamlit |
|----------------|-------|-----------|
| Upload de arquivo | ✅ | ✅ |
| Integração com API | ✅ | ✅ |
| Tabela editável | ✅ | ✅ |
| Histórico | ✅ | ✅ |
| Exportação | ✅ | ✅ |
| Estatísticas | ✅ | ✅ |

---

## ✅ Checklist

- [ ] Python 3.8+ instalado
- [ ] Dependências do backend instaladas
- [ ] Dependências do frontend instaladas
- [ ] API rodando em http://localhost:8000
- [ ] Streamlit rodando em http://localhost:8501
- [ ] Teste de upload funcionando

---

**Pronto! Agora você pode processar notas fiscais com Streamlit! 🎉**
