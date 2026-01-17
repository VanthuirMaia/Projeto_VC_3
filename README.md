# 📄 DocuExtract AI

Sistema inteligente de extração de dados de Notas Fiscais brasileiras (DANFE) utilizando OCR com múltiplos modelos pré-treinados e interface web moderna.

## 🎯 Sobre o Projeto

O **DocuExtract AI** é uma solução completa para extração automatizada de dados de Notas Fiscais Eletrônicas (NF-e) através de processamento de imagens e OCR. O sistema utiliza técnicas avançadas de pré-processamento de imagens e combina múltiplos engines OCR (EasyOCR, PaddleOCR, Tesseract) para maximizar a precisão na extração de dados estruturados.

## 🏗️ Arquitetura

O projeto é composto por duas partes principais:

### Backend (FastAPI)
- **Localização**: `Projeto_VC_3/`
- **Tecnologias**: FastAPI, EasyOCR, PaddleOCR, Tesseract, OpenCV
- **Funcionalidades**: 
  - Pré-processamento avançado de imagens
  - OCR com ensemble de múltiplos modelos
  - Extração estruturada de dados de NF-e
  - API REST com documentação interativa

### Frontend (Streamlit)
- **Localização**: `Interface/`
- **Tecnologias**: Streamlit, Python
- **Funcionalidades**:
  - Interface web moderna e responsiva
  - Upload de imagens/PDFs
  - Visualização e edição de dados extraídos
  - Exportação em JSON
  - Histórico de processamentos

## 🚀 Início Rápido

### Backend

```bash
cd Projeto_VC_3
pip install -r requirements.txt
python run_api.py
```

A API estará disponível em `http://localhost:8000`
Documentação: `http://localhost:8000/docs`

### Frontend

```bash
cd Interface
pip install -r requirements.txt
streamlit run app_docuextract.py
```

A interface estará disponível em `http://localhost:8501`

## 📚 Documentação

- **Instalação completa**: Veja `Projeto_VC_3/README.md`
- **Deploy**: Veja `DEPLOY_GITHUB.md` e `QUICK_DEPLOY.md`
- **Configuração**: Veja `ENV_EXAMPLE.md`
- **Documentação técnica completa**: Veja `Projeto_VC_3/DOCUMENTACAO_PROJETO.md`

## 🛠️ Tecnologias

- **Python 3.11+**
- **FastAPI** - API REST moderna e rápida
- **Streamlit** - Interface web interativa
- **EasyOCR** - OCR com deep learning
- **PaddleOCR** - OCR de alta precisão
- **Tesseract OCR** - OCR clássico e confiável
- **OpenCV** - Processamento de imagens
- **PyTorch** - Framework de deep learning

## 📋 Funcionalidades

✅ Pré-processamento avançado de imagens (deskew, denoise, binarização)  
✅ OCR com ensemble de 3 engines diferentes  
✅ Extração automática de campos de NF-e (CNPJ, valores, datas, etc.)  
✅ Validação de CNPJ/CPF com algoritmo de dígitos verificadores  
✅ Interface web responsiva e moderna  
✅ Exportação de dados em JSON  
✅ Histórico de processamentos  
✅ Cálculo de confiança por campo  

## 🌐 Deploy

O projeto está configurado para deploy em várias plataformas:

- **Streamlit Cloud** (Frontend) + **Railway** (Backend) - Recomendado
- **Render** (Backend + Frontend)
- **Docker** + **GitHub Actions**

Veja o guia completo em `DEPLOY_GITHUB.md` ou o guia rápido em `QUICK_DEPLOY.md`.

## 👥 Desenvolvedores

Este projeto foi desenvolvido por:

- **Karim Gomes**  
  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/karim-gomes-253023154/)

- **Rodrigo Santana**  
  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rodrigosantana94/)

- **Vanthuir Maia**  
  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vanthuir-maia-47767810b/)

## 📄 Licença

MIT

---

**DocuExtract AI** - *Extraindo dados com inteligência* 🤖
