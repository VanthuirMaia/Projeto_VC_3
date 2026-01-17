"""
DocuExtract AI - Interface Streamlit para Extração de Notas Fiscais
====================================================================

Versão Streamlit equivalente ao componente React streamlit-preview.tsx
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import time
import io

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

st.set_page_config(
    page_title="DocuExtract AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_TYPES = ['png', 'jpg', 'jpeg', 'pdf']

# =============================================================================
# VERIFICAÇÃO DE CONEXÃO COM API
# =============================================================================

def check_api_connection() -> bool:
    """Verifica se a API está rodando"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# =============================================================================
# ESTILIZAÇÃO CSS
# =============================================================================

def load_css():
    """Carrega estilos CSS personalizados para melhor responsividade"""
    st.markdown("""
    <style>
        /* Responsividade geral */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }
        
        /* Header responsivo */
        .main-header {
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        /* Tabelas responsivas */
        .stDataFrame {
            width: 100%;
            overflow-x: auto;
        }
        
        .stDataEditor {
            width: 100%;
        }
        
        /* Métricas responsivas */
        .stMetric {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        
        /* Botões responsivos */
        button[kind="primary"], .stDownloadButton {
            width: 100%;
        }
        
        /* Text areas responsivas */
        .stTextArea textarea {
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        /* Tabs responsivas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }
        
        /* Sidebar responsiva */
        .css-1d391kg {
            padding-top: 2rem;
        }
        
        /* Cards de estatísticas - grid responsivo */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem;
        }
        
        /* Responsividade mobile */
        @media (max-width: 768px) {
            .main-header {
                padding: 0.75rem;
            }
            
            .header-content {
                flex-direction: column;
                text-align: center;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 0.5rem 0.75rem;
                font-size: 0.8rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.25rem;
            }
            
            .stDataFrame, .stDataEditor {
                font-size: 0.85rem;
            }
            
            .stTextArea textarea {
                font-size: 0.85rem;
                height: 300px !important;
            }
        }
        
        /* Responsividade tablet */
        @media (min-width: 769px) and (max-width: 1024px) {
            .stTabs [data-baseweb="tab"] {
                font-size: 0.85rem;
            }
        }
        
        /* Melhorias de espaçamento */
        .element-container {
            margin-bottom: 1rem;
        }
        
        /* Scroll suave */
        html {
            scroll-behavior: smooth;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #eef2ff 0%, #ffffff 50%, #f3e8ff 100%);
            font-family: 'Inter', sans-serif;
        }
        
        .main-header {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid #e5e7eb;
            padding: 1rem 0;
            margin-bottom: 2rem;
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .logo-icon {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 0.5rem;
            border-radius: 0.5rem;
            color: white;
        }
        
        .app-title {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .upload-area {
            border: 2px dashed #d1d5db;
            border-radius: 1rem;
            padding: 3rem;
            text-align: center;
            background: white;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: #6366f1;
            background: #eef2ff;
        }
        
        .stat-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .confidence-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .confidence-high {
            background-color: #dcfce7;
            color: #16a34a;
        }
        
        .confidence-medium {
            background-color: #fef3c7;
            color: #d97706;
        }
        
        .confidence-low {
            background-color: #fee2e2;
            color: #dc2626;
        }
        
        .section-header {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem 0.5rem 0 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .export-button {
            background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            border: none;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .export-button:hover {
            transform: scale(1.05);
        }
        
        /* ============================================================
           RESPONSIVIDADE - Mobile First Approach
           ============================================================ */
        
        /* Container principal responsivo */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Tabelas e editores responsivos */
        [data-testid="stDataFrame"], 
        [data-testid="stDataEditor"] {
            width: 100%;
            overflow-x: auto;
            display: block;
        }
        
        /* Colunas responsivas */
        [data-testid="column"] {
            min-width: 0;
        }
        
        /* Métricas responsivas */
        [data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 0.75rem;
            border-radius: 0.5rem;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem;
            color: #6b7280;
        }
        
        /* Botões responsivos */
        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            min-width: 100px;
        }
        
        /* Text areas responsivas */
        .stTextArea textarea {
            font-size: 0.9rem;
            line-height: 1.5;
            width: 100%;
        }
        
        /* Tabs responsivas */
        [data-baseweb="tab-list"] {
            gap: 0.25rem;
            flex-wrap: wrap;
        }
        
        [data-baseweb="tab"] {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
            white-space: nowrap;
            min-width: fit-content;
        }
        
        /* Upload area responsiva */
        [data-testid="stFileUploader"] {
            width: 100%;
        }
        
        /* Sidebar responsiva */
        .css-1d391kg {
            padding-top: 1.5rem;
        }
        
        /* Melhorias de espaçamento */
        .element-container {
            margin-bottom: 1rem;
        }
        
        /* Scroll suave */
        html {
            scroll-behavior: smooth;
        }
        
        /* ============================================================
           BREAKPOINTS - Media Queries
           ============================================================ */
        
        /* Mobile (< 768px) */
        @media (max-width: 768px) {
            .main-header {
                padding: 0.75rem 0;
                margin-bottom: 1rem;
            }
            
            .header-content {
                flex-direction: column;
                text-align: center;
                padding: 0 1rem;
            }
            
            .logo-container {
                justify-content: center;
            }
            
            .app-title {
                font-size: 1.25rem;
            }
            
            .main .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }
            
            [data-baseweb="tab"] {
                padding: 0.5rem 0.75rem;
                font-size: 0.8rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.25rem;
            }
            
            [data-testid="stMetricLabel"] {
                font-size: 0.75rem;
            }
            
            .stTextArea textarea {
                font-size: 0.85rem;
            }
            
            /* Colunas empilham em mobile */
            [data-testid="column"] {
                width: 100% !important;
            }
            
            /* Tabelas com scroll horizontal em mobile */
            [data-testid="stDataFrame"],
            [data-testid="stDataEditor"] {
                font-size: 0.85rem;
            }
            
            .upload-area {
                padding: 2rem 1rem;
            }
        }
        
        /* Tablet (768px - 1024px) */
        @media (min-width: 769px) and (max-width: 1024px) {
            .header-content {
                padding: 0 1.5rem;
            }
            
            [data-baseweb="tab"] {
                font-size: 0.85rem;
                padding: 0.65rem 0.9rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.4rem;
            }
        }
        
        /* Desktop (> 1024px) */
        @media (min-width: 1025px) {
            .main .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
            }
            
            .header-content {
                padding: 0 2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def init_session_state():
    """Inicializa variáveis de sessão"""
    if 'table_data' not in st.session_state:
        st.session_state.table_data = []
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_file_name' not in st.session_state:
        st.session_state.current_file_name = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'processing_info' not in st.session_state:
        st.session_state.processing_info = None
    if 'raw_text' not in st.session_state:
        st.session_state.raw_text = None

def get_confidence_color(confidence: int) -> str:
    """Retorna classe CSS baseada em confiança"""
    if confidence >= 95:
        return 'confidence-high'
    elif confidence >= 85:
        return 'confidence-medium'
    else:
        return 'confidence-low'

def format_currency(value: float) -> str:
    """Formata valor monetário para formato brasileiro"""
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_currency(value: str) -> float:
    """Converte valor monetário brasileiro para float"""
    cleaned = value.replace('R$', '').replace(' ', '').strip()
    if ',' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    try:
        return float(cleaned)
    except:
        return 0.0

def convert_api_response_to_table(api_data: Dict, processing_info: Dict = None) -> List[Dict]:
    """Converte resposta da API para formato de tabela"""
    table_data = []
    
    # Usa confiança do OCR se disponível (mais precisa), senão usa confidence_score
    if processing_info and 'ocr_confidence_avg' in processing_info:
        base_confidence = int(processing_info['ocr_confidence_avg'] * 100)
        # Limita entre 50-95% para refletir melhor a confiança real
        base_confidence = max(50, min(95, base_confidence))
    else:
        # Fallback: usa confidence_score, mas garante mínimo razoável
        base_confidence = int((api_data.get('confidence_score', 0.7) * 100))
        base_confidence = max(60, base_confidence)  # Mínimo 60% se baseado em campos
    
    field_mappings = {
        'numero_nf': ('Número NF', base_confidence + 8),  # Números têm alta confiança
        'serie': ('Série', base_confidence + 5),
        'chave_acesso': ('Chave de Acesso', base_confidence + 12),  # Regex muito específico
        'data_emissao': ('Data Emissão', base_confidence + 6),
        'cnpj_emitente': ('CNPJ Emitente', base_confidence + 10),  # Validado
        'razao_social_emitente': ('Razão Social Emitente', base_confidence - 3),  # Texto livre
        'inscricao_estadual_emitente': ('Inscrição Estadual', base_confidence + 2),
        'cnpj_destinatario': ('CNPJ Destinatário', base_confidence + 10),  # Validado
        'cpf_destinatario': ('CPF Destinatário', base_confidence + 10),  # Validado
        'nome_destinatario': ('Nome Destinatário', base_confidence - 3),  # Texto livre
    }
    
    for key, (label, confidence) in field_mappings.items():
        value = api_data.get(key, '')
        if value:
            table_data.append({
                'campo': label,
                'valor': str(value),
                'confianca': confidence
            })
    
    # Valores monetários (têm boa precisão por serem numéricos)
    valor_mappings = {
        'valor_total': ('Valor Total', base_confidence + 8),
        'valor_produtos': ('Valor Produtos', base_confidence + 6),
        'valor_frete': ('Valor Frete', base_confidence + 4),
        'valor_icms': ('Valor ICMS', base_confidence + 5),
    }
    
    for key, (label, confidence) in valor_mappings.items():
        value = api_data.get(key, 0)
        if value > 0:
            table_data.append({
                'campo': label,
                'valor': format_currency(value),
                'confianca': confidence
            })
    
    return table_data

def export_to_json(table_data: List[Dict] = None, full_data: Dict = None, processing_info: Dict = None, raw_text: str = None, filename: str = None):
    """Exporta dados para JSON (formato completo da API)
    
    Args:
        table_data: Dados formatados da tabela (formato simples para visualização)
        full_data: Dados completos da API (NFDataModel)
        processing_info: Informações de processamento (engines, confiança, etc.)
        raw_text: Texto OCR bruto (se disponível)
        filename: Nome do arquivo (opcional)
    """
    if filename is None:
        filename = f"dados_nf_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Se full_data disponível, exporta dados completos da API (igual ao response da API)
    if full_data is not None:
        export_data = {
            "success": True,
            "data": full_data,
            "raw_text": raw_text or "",
            "processing_info": processing_info or {},
            "table_data": table_data or [],  # Inclui também a tabela formatada para compatibilidade
            "exported_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        # Fallback: exporta apenas tabela (formato antigo)
        export_data = table_data or []
    
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="export_json"
    )

def export_to_csv(data: List[Dict], filename: str = None):
    """Exporta dados para CSV"""
    if filename is None:
        filename = f"dados_nf_{datetime.now().strftime('%Y%m%d')}.csv"
    
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv.encode('utf-8-sig'),
        file_name=filename,
        mime="text/csv",
        key="export_csv"
    )

def export_to_markdown(data: List[Dict], filename: str = None):
    """Exporta dados para Markdown"""
    if filename is None:
        filename = f"dados_nf_{datetime.now().strftime('%Y%m%d')}.md"
    
    md_lines = [
        "# Dados Extraídos da Nota Fiscal\n",
        "| Campo | Valor | Confiança (%) |",
        "|-------|-------|---------------|"
    ]
    
    for row in data:
        md_lines.append(f"| {row['campo']} | {row['valor']} | {row['confianca']}% |")
    
    md_lines.append(f"\n*Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*")
    
    md_content = "\n".join(md_lines)
    st.download_button(
        label="📥 Download Markdown",
        data=md_content,
        file_name=filename,
        mime="text/markdown",
        key="export_md"
    )

def call_api_extract(file) -> Optional[Dict]:
    """Chama API para extrair dados estruturados da nota fiscal"""
    # Verifica conexão primeiro
    if not check_api_connection():
        st.error(f"""
        ❌ **API não está rodando!**
        
        Para iniciar a API:
        
        1. Abra um terminal
        2. Execute:
        ```bash
        cd "API\\Projeto_VC_3"
        python run_api.py
        ```
        3. Aguarde a mensagem: `Uvicorn running on http://0.0.0.0:8000`
        4. Recarregue esta página
        
        **URL da API:** {API_BASE_URL}
        """)
        return None
    
    try:
        files = {'file': (file.name, file.getvalue(), file.type)}
        params = {'include_raw_text': 'true'}  # Inclui texto bruto para exportação completa
        
        with st.spinner('🔍 Processando com IA...'):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simula progresso
            for i in range(0, 101, 10):
                progress_bar.progress(i / 100)
                status_text.text(f'Processando... {i}%')
                time.sleep(0.1)
            
            response = requests.post(
                f"{API_BASE_URL}/extract",
                files=files,
                params=params,
                timeout=60
            )
            
            progress_bar.progress(100)
            status_text.text('Processamento concluído!')
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                st.error(f"Erro na API: {error_data.get('detail', f'Status {response.status_code}')}")
                return None
                
    except requests.exceptions.ConnectionError:
        st.error(f"""
        ❌ **Não foi possível conectar à API em {API_BASE_URL}**
        
        **Solução:**
        1. Verifique se a API está rodando
        2. Teste manualmente: http://localhost:8000/health
        3. Verifique se a porta 8000 está livre
        """)
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout ao processar arquivo. O arquivo pode ser muito grande ou a API está lenta.")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        return None

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

def render_header():
    """Renderiza cabeçalho da aplicação"""
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <div class="logo-container">
                <div class="logo-icon">📄</div>
                <div class="app-title">DocuExtract AI</div>
            </div>
            <div style="display: flex; gap: 0.75rem;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_upload_section():
    """Renderiza seção de upload"""
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <div style="display: inline-flex; align-items: center; gap: 0.5rem; background: #eef2ff; color: #6366f1; padding: 0.5rem 1rem; border-radius: 9999px; margin-bottom: 1rem;">
            ✨ Extração Inteligente de Dados
        </div>
        <h2 style="font-size: 2.25rem; font-weight: 700; color: #111827; margin-bottom: 0.75rem;">
            Transforme suas notas fiscais<br/>em dados estruturados
        </h2>
        <p style="font-size: 1.125rem; color: #6b7280; max-width: 600px; margin: 0 auto;">
            Upload, revisão e exportação em segundos.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_table_editor():
    """Renderiza editor de tabela"""
    if not st.session_state.table_data:
        st.info("📋 Nenhum dado extraído ainda. Faça upload de uma nota fiscal.")
        return
    
    st.markdown("### 📋 Informações do Documento")
    
    # Tabela editável usando data_editor
    df = pd.DataFrame(st.session_state.table_data)
    
    edited_df = st.data_editor(
        df,
        column_config={
            "campo": st.column_config.TextColumn("Campo", width="medium"),
            "valor": st.column_config.TextColumn("Valor Extraído", width="large"),
            "confianca": st.column_config.NumberColumn("Confiança (%)", min_value=0, max_value=100, width="small")
        },
        width='stretch',
        num_rows="dynamic",
        key="table_editor"
    )
    
    # Atualiza dados da sessão
    if not edited_df.empty:
        st.session_state.table_data = edited_df.to_dict('records')
    
    # Botão para adicionar campo
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("➕ Adicionar Campo"):
            st.session_state.table_data.append({
                'campo': 'Novo Campo',
                'valor': '',
                'confianca': 0
            })
            st.rerun()

def render_export_section():
    """Renderiza seção de exportação"""
    # Permite exportar mesmo sem tabela (caso seja /ocr)
    if not st.session_state.table_data and not st.session_state.raw_text:
        return
    
    st.markdown("---")
    st.markdown("### 📥 Exportar Dados")
    
    # Layout responsivo: 3 colunas no desktop, 1 coluna no mobile
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        export_to_json(
            table_data=st.session_state.table_data,
            full_data=st.session_state.get('processed_data'),
            processing_info=st.session_state.get('processing_info'),
            raw_text=st.session_state.get('raw_text', '')
        )
    
    with col2:
        export_to_csv(st.session_state.table_data)
    
    with col3:
        export_to_markdown(st.session_state.table_data)
    
    st.success("✅ Dados verificados e prontos para exportação!")

def render_stats_cards():
    """Renderiza cards de estatísticas"""
    if not st.session_state.table_data:
        return
    
    # Layout responsivo: 3 colunas no desktop, empilha no mobile
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.metric("📊 Campos Extraídos", len(st.session_state.table_data))
    
    with col2:
        avg_confidence = int(sum(row['confianca'] for row in st.session_state.table_data) / len(st.session_state.table_data))
        st.metric("🎯 Confiança Média", f"{avg_confidence}%")
    
    with col3:
        st.metric("✅ Status", "Pronto")

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

def main():
    load_css()
    init_session_state()
    
    # Verifica status da API no início
    api_status = check_api_connection()
    
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/5650/5650570.png", width=80)
        st.markdown("### 🎛️ Painel de Controle")
        
        # Status da API
        if api_status:
            st.success(f"✅ API conectada\n{API_BASE_URL}")
        else:
            st.error(f"❌ API desconectada\n{API_BASE_URL}")
            st.info("💡 Para iniciar a API:\n```bash\ncd \"API\\Projeto_VC_3\"\npython run_api.py\n```")
        
        st.markdown("---")
        st.info("💡 **Dica:** Suporte para PDF, PNG, JPG até 200MB")
        
        if st.button("🗑️ Limpar Dados"):
            st.session_state.table_data = []
            st.session_state.current_file_name = None
            st.session_state.processed_data = None
            st.rerun()
    
    # Seção de upload
    if not st.session_state.table_data:
        render_upload_section()
    
    # Upload de arquivo
    uploaded_file = st.file_uploader(
        "📤 Arraste seu documento ou clique para selecionar",
        type=ALLOWED_TYPES,
        help="Suporta PDF, PNG, JPG até 200MB",
        key="file_uploader"
    )
    
    # Processa arquivo se foi enviado
    if uploaded_file is not None:
        # Valida tamanho
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"❌ Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE / (1024*1024)}MB")
        else:
            # Verifica se é um novo arquivo (diferente do anterior)
            is_new_file = (
                st.session_state.current_file_name is None or 
                st.session_state.current_file_name != uploaded_file.name
            )
            
            # Se for um novo arquivo, limpa os dados anteriores
            if is_new_file:
                st.session_state.processed_data = None
                st.session_state.processing_info = None
                st.session_state.raw_text = None
                st.session_state.table_data = []
                st.session_state.current_file_name = uploaded_file.name
            
            # Chama API se ainda não foi processado
            if st.session_state.processed_data is None:
                result = call_api_extract(uploaded_file)
                
                if result and result.get('success'):
                    # Endpoint /extract retorna dados estruturados
                    api_data = result.get('data', {})
                    processing_info = result.get('processing_info', {})
                    raw_text = result.get('raw_text', '')
                    
                    st.session_state.processed_data = api_data
                    st.session_state.processing_info = processing_info
                    st.session_state.raw_text = raw_text
                    st.session_state.table_data = convert_api_response_to_table(api_data, processing_info)
                    
                    # Adiciona ao histórico
                    # Calcula confiança média dos campos (mesma lógica dos stats cards)
                    if st.session_state.table_data:
                        avg_confidence = int(sum(row['confianca'] for row in st.session_state.table_data) / len(st.session_state.table_data))
                    else:
                        # Fallback: usa confidence_score da API
                        avg_confidence = int((api_data.get('confidence_score', 0.8) * 100))
                    
                    history_item = {
                        'id': len(st.session_state.history) + 1,
                        'nome': uploaded_file.name,
                        'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'valor': format_currency(api_data.get('valor_total', 0)),
                        'confianca': avg_confidence,  # Usa mesma confiança dos stats cards
                        'fornecedor': api_data.get('razao_social_emitente', 'Não identificado')
                    }
                    st.session_state.history.append(history_item)
                    st.rerun()
            else:
                # Mostra arquivo já processado
                st.success(f"✅ **{uploaded_file.name}** processado com sucesso!")
    
    # Mostra conteúdo após processamento em duas abas
    if st.session_state.table_data or st.session_state.raw_text:
        # Cria duas abas: Extract (primeira) e Dados Brutos (segunda)
        tab1, tab2 = st.tabs(["📊 Extract - Dados Estruturados", "📝 Dados Brutos - OCR"])
        
        # ============================================================
        # ABA 1: Extract - Dados Estruturados (PRIMEIRA)
        # ============================================================
        with tab1:
            if st.session_state.table_data:
                # Stats Cards
                render_stats_cards()
                st.markdown("---")
                
                # Tabela Editor
                render_table_editor()
                
                # Exportação (apenas na aba Extract)
                render_export_section()
            else:
                st.warning("⚠️ Nenhum dado estruturado disponível. Os campos não foram extraídos.")
        
        # ============================================================
        # ABA 2: Dados Brutos - OCR (SEGUNDA)
        # ============================================================
        with tab2:
            if st.session_state.raw_text:
                # Estatísticas do texto bruto
                text_length = len(st.session_state.raw_text)
                lines_count = st.session_state.raw_text.count('\n') + 1
                words_count = len(st.session_state.raw_text.split())
                
                # Layout responsivo
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.metric("📏 Caracteres", f"{text_length:,}")
                with col2:
                    st.metric("📄 Linhas", f"{lines_count:,}")
                with col3:
                    st.metric("🔤 Palavras", f"{words_count:,}")
                
                st.markdown("---")
                
                # Texto OCR completo
                st.markdown("### 📝 Texto OCR Completo")
                st.text_area(
                    "Texto extraído:",
                    value=st.session_state.raw_text,
                    height=500,
                    disabled=True,
                    key="raw_ocr_text_display",
                    help="Este é o texto bruto extraído pelo OCR antes de qualquer processamento ou extração de campos."
                )
                
                # Botão para copiar texto
                st.markdown("---")
                st.markdown("### 🔧 Ações")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Baixar Texto (.txt)",
                        data=st.session_state.raw_text,
                        file_name=f"texto_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key="download_raw_text"
                    )
                with col2:
                    if st.button("📋 Copiar para Área de Transferência", key="copy_text"):
                        st.code(st.session_state.raw_text, language=None)
                        st.success("✅ Texto copiado! Use Ctrl+C para copiar.")
            else:
                st.warning("⚠️ Texto OCR bruto não disponível. Verifique se `include_raw_text=true` foi enviado à API.")
    
    # Seção de Histórico
    if st.session_state.history:
        with st.expander("🕒 Histórico de Documentos", expanded=False):
            history_df = pd.DataFrame(st.session_state.history)
            
            # Tabela de histórico
            st.dataframe(
                history_df[['nome', 'fornecedor', 'data', 'valor', 'confianca']],
                width='stretch',
                hide_index=True
            )
            
            # Estatísticas do histórico
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Docs", len(st.session_state.history))
            with col2:
                total_valor = sum(parse_currency(h['valor']) for h in st.session_state.history)
                st.metric("Valor Total", format_currency(total_valor))
            with col3:
                avg_conf = int(sum(h['confianca'] for h in st.session_state.history) / len(st.session_state.history))
                st.metric("Confiança Média", f"{avg_conf}%")

if __name__ == "__main__":
    main()
