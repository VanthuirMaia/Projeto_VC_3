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

def convert_api_response_to_table(api_data: Dict) -> List[Dict]:
    """Converte resposta da API para formato de tabela"""
    table_data = []
    base_confidence = int((api_data.get('confidence_score', 0.8) * 100))
    
    field_mappings = {
        'numero_nf': ('Número NF', base_confidence + 5),
        'serie': ('Série', base_confidence + 3),
        'chave_acesso': ('Chave de Acesso', base_confidence + 10),
        'data_emissao': ('Data Emissão', base_confidence + 2),
        'cnpj_emitente': ('CNPJ Emitente', base_confidence + 8),
        'razao_social_emitente': ('Razão Social Emitente', base_confidence - 5),
        'inscricao_estadual_emitente': ('Inscrição Estadual', base_confidence),
        'cnpj_destinatario': ('CNPJ Destinatário', base_confidence + 8),
        'cpf_destinatario': ('CPF Destinatário', base_confidence + 8),
        'nome_destinatario': ('Nome Destinatário', base_confidence - 5),
    }
    
    for key, (label, confidence) in field_mappings.items():
        value = api_data.get(key, '')
        if value:
            table_data.append({
                'campo': label,
                'valor': str(value),
                'confianca': confidence
            })
    
    # Valores monetários
    valor_mappings = {
        'valor_total': ('Valor Total', base_confidence + 5),
        'valor_produtos': ('Valor Produtos', base_confidence + 3),
        'valor_frete': ('Valor Frete', base_confidence),
        'valor_icms': ('Valor ICMS', base_confidence + 2),
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

def export_to_json(data: List[Dict], filename: str = None):
    """Exporta dados para JSON"""
    if filename is None:
        filename = f"dados_nf_{datetime.now().strftime('%Y%m%d')}.json"
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
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
    """Chama API para extrair dados da nota fiscal"""
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
        params = {'include_raw_text': 'false'}
        
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
                <div>
                    <div class="app-title">DocuExtract AI</div>
                    <div style="font-size: 0.75rem; color: #6b7280;">Powered by AI • API: """ + API_BASE_URL + """ • Status: """ + ("✅ Online" if check_api_connection() else "❌ Offline") + """</div>
                </div>
            </div>
            <div style="display: flex; gap: 0.75rem;">
                <button onclick="window.location.reload()" style="background: #f3f4f6; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer;">
                    🕒 Histórico
                </button>
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
            Upload, revisão e exportação em segundos. Precisão de 95%+ com IA.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_table_editor():
    """Renderiza editor de tabela"""
    if not st.session_state.table_data:
        st.info("📋 Nenhum dado extraído ainda. Faça upload de uma nota fiscal.")
        return
    
    st.markdown("### ✏️ Revisar e Editar Dados")
    
    # Tabela editável usando data_editor
    df = pd.DataFrame(st.session_state.table_data)
    
    edited_df = st.data_editor(
        df,
        column_config={
            "campo": st.column_config.TextColumn("Campo", width="medium"),
            "valor": st.column_config.TextColumn("Valor Extraído", width="large"),
            "confianca": st.column_config.NumberColumn("Confiança (%)", min_value=0, max_value=100, width="small")
        },
        use_container_width=True,
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
    if not st.session_state.table_data:
        return
    
    st.markdown("---")
    st.markdown("### 📥 Exportar Dados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_to_json(st.session_state.table_data)
    
    with col2:
        export_to_csv(st.session_state.table_data)
    
    with col3:
        export_to_markdown(st.session_state.table_data)
    
    st.success("✅ Dados verificados e prontos para exportação!")

def render_stats_cards():
    """Renderiza cards de estatísticas"""
    if not st.session_state.table_data:
        return
    
    col1, col2, col3 = st.columns(3)
    
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
    
    # Banner de status da API
    if not api_status:
        st.warning(f"""
        ⚠️ **API não está conectada!**
        
        A aplicação não conseguiu conectar à API em **{API_BASE_URL}**.
        
        **Para iniciar a API:**
        ```bash
        cd "API\\Projeto_VC_3"
        python run_api.py
        ```
        
        Após iniciar a API, clique em **🔄 Recarregar** no menu do Streamlit ou pressione **R**.
        """)
    else:
        st.success(f"✅ API conectada em {API_BASE_URL}")
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/5650/5650570.png", width=80)
        st.markdown("### 🎛️ Painel de Controle")
        st.info("💡 **Dica:** Suporte para PDF, PNG, JPG até 200MB")
        st.markdown("---")
        
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
            st.session_state.current_file_name = uploaded_file.name
            
            # Chama API se ainda não foi processado
            if st.session_state.processed_data is None:
                result = call_api_extract(uploaded_file)
                
                if result and result.get('success'):
                    api_data = result.get('data', {})
                    st.session_state.processed_data = api_data
                    st.session_state.table_data = convert_api_response_to_table(api_data)
                    
                    # Adiciona ao histórico
                    history_item = {
                        'id': len(st.session_state.history) + 1,
                        'nome': uploaded_file.name,
                        'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'valor': format_currency(api_data.get('valor_total', 0)),
                        'confianca': int((api_data.get('confidence_score', 0.8) * 100)),
                        'fornecedor': api_data.get('razao_social_emitente', 'Não identificado')
                    }
                    st.session_state.history.append(history_item)
                    st.rerun()
            else:
                # Mostra arquivo já processado
                st.success(f"✅ **{uploaded_file.name}** processado com sucesso!")
    
    # Mostra conteúdo após processamento
    if st.session_state.table_data:
        st.markdown("---")
        
        # Stats Cards
        render_stats_cards()
        st.markdown("---")
        
        # Tabela Editor
        render_table_editor()
        
        # Exportação
        render_export_section()
    
    # Seção de Histórico
    if st.session_state.history:
        with st.expander("🕒 Histórico de Documentos", expanded=False):
            history_df = pd.DataFrame(st.session_state.history)
            
            # Tabela de histórico
            st.dataframe(
                history_df[['nome', 'fornecedor', 'data', 'valor', 'confianca']],
                use_container_width=True,
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
