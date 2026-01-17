import streamlit as st
from PIL import Image, ImageFilter
import numpy as np
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Veritas ArtLab",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS AVANÇADA ---
def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600&display=swap');
        .stApp {
            background-color: #0E1117;
            background-image: linear-gradient(180deg, #0E1117 0%, #161B22 100%);
            color: #E0E0E0;
        }
        h1, h2, h3 { font-family: 'Cinzel', serif !important; font-weight: 700; }
        p, div, label, button { font-family: 'Montserrat', sans-serif !important; }
        .main-title {
            font-size: 3.5rem; text-align: center;
            background: -webkit-linear-gradient(#D4AF37, #F8F8FF);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.3);
        }
        .subtitle { text-align: center; font-size: 1.2rem; color: #888; margin-bottom: 40px; letter-spacing: 2px; }
        .verdict-card {
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px; padding: 30px; text-align: center;
            backdrop-filter: blur(10px); box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); margin-bottom: 20px;
        }
        .seal-human { border: 3px solid #D4AF37; color: #D4AF37; box-shadow: 0 0 25px rgba(212, 175, 55, 0.4); }
        .seal-ai { border: 3px solid #00FFFF; color: #00FFFF; box-shadow: 0 0 25px rgba(0, 255, 255, 0.4); }
        .verdict-seal {
            width: 180px; height: 180px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center; margin: 0 auto 20px auto;
            font-family: 'Cinzel', serif; font-weight: bold; font-size: 1.5rem;
            text-transform: uppercase; letter-spacing: 2px; background: rgba(0,0,0,0.3);
        }
        .stProgress > div > div > div > div { background-image: linear-gradient(to right, #D4AF37, #00FFFF); }
        .stFileUploader { border: 1px dashed #444; border-radius: 10px; padding: 20px; }
        [data-testid="stSidebar"] { background-color: #0b0d10; border-right: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

local_css()

def mock_analyze_image(image):
    time.sleep(2)
    is_ai_prob = 0.94
    return is_ai_prob

def apply_heatmap_overlay(image):
    img_array = np.array(image.convert('RGBA'))
    overlay = np.zeros_like(img_array)
    overlay[:, :, 0] = 255
    overlay[:, :, 3] = 0
    h, w = img_array.shape[:2]
    center_y, center_x = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    mask = (x - center_x)**2 + (y - center_y)**2 <= (min(h, w) // 3)**2
    overlay[mask, 3] = 120
    overlay_img = Image.fromarray(overlay)
    return Image.alpha_composite(image.convert('RGBA'), overlay_img)

def apply_texture_analysis(image):
    return image.filter(ImageFilter.FIND_EDGES)

st.markdown('<h1 class="main-title">VERITAS ARTLAB</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">SISTEMA FORENSE DE AUTENTICAÇÃO DE ARTE</p>', unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/5650/5650570.png", width=60)
    st.markdown("### Painel de Controle")
    st.info("💡 **Dica:** Imagens > 1080p oferecem melhores resultados.")
    st.markdown("---")
    reset_btn = st.button("Nova Análise")

if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

if reset_btn:
    st.session_state.analyzed = False
    st.session_state.prob_ai = None
    st.rerun()

uploaded_file = st.file_uploader("Apresente a obra para autenticação", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    if not st.session_state.analyzed:
        with st.spinner('🔍 Analisando padrões...'):
            st.session_state.prob_ai = mock_analyze_image(image)
            st.session_state.analyzed = True

    col1, col2 = st.columns([2, 1.2])
    with col1:
        st.markdown("### 👁️ Visualização Espectral")
        filter_mode = st.radio("Camada:", ("Original", "Mapa de Calor", "Textura"), horizontal=True)
        final_display = image
        if filter_mode == "Mapa de Calor":
            final_display = apply_heatmap_overlay(image)
        elif filter_mode == "Textura":
            final_display = apply_texture_analysis(image)
        st.image(final_display, use_container_width=True)

    with col2:
        st.markdown("### ⚖️ Veredito")
        prob = st.session_state.prob_ai
        is_ai = prob > 0.5
        seal_class, verdict_text, color = ("seal-ai", "GERADO POR IA", "#00FFFF") if is_ai else ("seal-human", "ARTE HUMANA", "#D4AF37")
        st.markdown(f"""
        <div class="verdict-card">
            <div class="verdict-seal {seal_class}">{verdict_text}</div>
            <h2 style="color: {color};">{int(prob*100) if is_ai else int((1-prob)*100)}% CONFIANÇA</h2>
        </div>
        """, unsafe_allow_html=True)
        st.progress(int(prob * 100))
        st.markdown("#### 📊 Métricas Detalhadas")
        m1, m2 = st.columns(2)
        m1.metric("Ruído", "Alta" if is_ai else "Baixa")
        m2.metric("Luz", "Suspeito" if is_ai else "Normal")
else:
    st.markdown("<h3 style='text-align:center; color:#555;'>Aguardando submissão...</h3>", unsafe_allow_html=True)
