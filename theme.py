"""Estilo visual do app: CSS injetado por cima do tema base (.streamlit/config.toml)
para uma aparência mais refinada -- tipografia com serifa nos títulos, cartões com
borda/sombra sutil, botões mais sóbrios.

Chamado uma única vez em Home.py, que sempre roda primeiro (mesmo em subpáginas) e
também antes do login, então a identidade visual já aparece na tela de entrada.
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Títulos com serifa -- dá um ar mais autoral/boutique, sem perder legibilidade */
div[data-testid="stAppViewContainer"] h1,
div[data-testid="stAppViewContainer"] h2,
div[data-testid="stAppViewContainer"] h3 {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #2b1b20;
}
div[data-testid="stAppViewContainer"] h1 { font-size: 2rem; }

/* Barra lateral: fundo neutro, separada por uma linha fina em vez de cor forte */
section[data-testid="stSidebar"] {
    background-color: #fbf8f6;
    border-right: 1px solid #e8dcdf;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-family: 'Inter', sans-serif;
}

/* Botões: cantos discretos, sombra leve, sem gradientes chamativos */
.stButton button, .stFormSubmitButton button, [data-testid="stDownloadButton"] button {
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.01em;
    box-shadow: 0 1px 2px rgba(43, 27, 32, 0.10);
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.stButton button:hover, .stFormSubmitButton button:hover, [data-testid="stDownloadButton"] button:hover {
    box-shadow: 0 3px 8px rgba(43, 27, 32, 0.16);
    transform: translateY(-1px);
}

/* Campos de preenchimento: o Streamlit desenha a borda dos campos em branco
   por padrão (invisível sobre fundo branco/cartão) -- aqui ela vira visível,
   com um realce claro ao focar */
div[data-testid="stTextInputRootElement"],
div[data-testid="stTextAreaRootElement"],
div[data-testid="stNumberInputContainer"],
div[data-testid="stDateInputField"],
div[data-testid="stSelectbox"] div:has(> input) {
    border: 1px solid #c9a8b2 !important;
    background-color: #fdfbfa !important;
    border-radius: 8px !important;
}
div[data-testid="stTextInputRootElement"]:focus-within,
div[data-testid="stTextAreaRootElement"]:focus-within,
div[data-testid="stNumberInputContainer"]:focus-within,
div[data-testid="stDateInputField"]:focus-within,
div[data-testid="stSelectbox"] div:has(> input):focus-within {
    border-color: #8c2f52 !important;
    box-shadow: 0 0 0 1px #8c2f52 !important;
}

/* Cartões: métricas, formulários, expanders e abas com borda/sombra sutis */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e8dcdf;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    box-shadow: 0 1px 3px rgba(43, 27, 32, 0.05);
}
div[data-testid="stForm"] {
    border: 1px solid #e8dcdf;
    border-radius: 12px;
    padding: 1.25rem;
    background: #ffffff;
}
div[data-testid="stExpander"] {
    border: 1px solid #e8dcdf;
    border-radius: 10px;
    overflow: hidden;
}

/* Cabeçalho superior (barra "Deploy"/menu) neutro, sem contraste forte */
header[data-testid="stHeader"] {
    background: transparent;
}

/* Caption/legenda um pouco mais discreta */
div[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
    color: #6b5a5e;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
