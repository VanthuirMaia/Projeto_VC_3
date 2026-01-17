# 🎨 Veritas ArtLab

Sistema Forense de Autenticação de Arte - Uma aplicação web moderna para análise e detecção de arte gerada por IA versus arte humana.

## 📋 Descrição

Veritas ArtLab é uma interface web desenvolvida com Streamlit que permite analisar imagens e determinar se foram geradas por Inteligência Artificial ou criadas por artistas humanos. A aplicação oferece visualizações espectrais avançadas e métricas detalhadas para análise forense de arte.

## ✨ Funcionalidades

- 📤 **Upload de Imagens**: Suporte para PNG, JPG e JPEG
- 🔍 **Análise Forense**: Detecção de padrões que indicam geração por IA
- 👁️ **Visualização Espectral**: Três modos de visualização:
  - Original
  - Mapa de Calor
  - Análise de Textura (detecção de bordas)
- ⚖️ **Veredito Visual**: Exibição clara do resultado com percentual de confiança
- 📊 **Métricas Detalhadas**: Análise de ruído e padrões de luz
- 🎨 **Interface Moderna**: Design elegante com tema escuro e tipografia personalizada

## 🛠️ Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 📦 Instalação

1. **Clone ou baixe este repositório**

2. **Crie um ambiente virtual (recomendado)**

   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Como Executar

1. **Ative o ambiente virtual** (se estiver usando)

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

2. **Execute a aplicação**
   ```bash
   streamlit run app.py
   ```

3. **Acesse no navegador**

   A aplicação será aberta automaticamente no navegador em:
   ```
   http://localhost:8501
   ```

   Se não abrir automaticamente, copie e cole o endereço no seu navegador.

## 📁 Estrutura do Projeto

```
Interface/
│
├── app.py                 # Aplicação principal Streamlit
├── requirements.txt       # Dependências do projeto
└── README.md             # Este arquivo
```

## 📚 Tecnologias Utilizadas

- **Streamlit**: Framework para criação de aplicações web em Python
- **Pillow (PIL)**: Biblioteca para processamento de imagens
- **NumPy**: Biblioteca para cálculos numéricos e manipulação de arrays
- **HTML/CSS**: Estilização avançada com fonts personalizadas (Google Fonts)

## 💡 Como Usar

1. **Inicie a aplicação** seguindo os passos acima
2. **Faça upload de uma imagem** usando o seletor de arquivos
3. **Aguarde a análise** (aproximadamente 2 segundos)
4. **Explore as visualizações** alternando entre Original, Mapa de Calor e Textura
5. **Visualize o veredito** com percentual de confiança e métricas detalhadas
6. **Use o botão "Nova Análise"** na sidebar para analisar outra imagem

## 📝 Notas

- Para melhores resultados, use imagens com resolução maior que 1080p
- A análise atual utiliza uma função mock (simulada) - idealmente, deve ser substituída por um modelo de IA treinado
- O sistema armazena o resultado da análise em sessão até que uma nova análise seja solicitada

## 🔧 Troubleshooting

**Problema**: Erro ao instalar dependências
- **Solução**: Certifique-se de estar usando Python 3.8+ e pip atualizado
  ```bash
  python --version
  pip install --upgrade pip
  ```

**Problema**: Porta 8501 já em uso
- **Solução**: Streamlit tentará usar outra porta automaticamente. Verifique o terminal para o novo endereço.

**Problema**: Imagem não carrega
- **Solução**: Verifique se o formato é PNG, JPG ou JPEG e se o arquivo não está corrompido.

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais.

## 👨‍💻 Autor

Desenvolvido como parte da Atividade 3 de Visão Computacional.

---

**Veritas ArtLab** - *Autenticando a verdade na arte* 🎭
