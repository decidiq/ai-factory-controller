"""Gaya tampilan Decidiq — Modern Gradient Theme."""
import streamlit as st

CSS = """
<style>
/* ============================================
   FORCE OVERRIDE STREAMLIT THEME VARIABLES
   ============================================ */
:root {
    --primary-color: #8B5CF6;
    --secondary-background-color: #FFFFFF;
    --background-color: #FAFAFA;
    --text-color: #0F172A;
}

[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    --secondary-background-color: #4C1D95 !important;
    --text-color: #FFFFFF !important;
    --background-color: #1E1B4B !important;
    --primary-color: #8B5CF6 !important;
}

/* === RESET === */
* { box-sizing: border-box; }
.stApp {
    background: #FAFAFA;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #0F172A;
}

/* ============================================
   SIDEBAR BACKGROUND
   ============================================ */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #1E1B4B 0%, #312E81 100%) !important;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] {
    min-width: 280px !important;
    max-width: 280px !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #E9D5FF !important;
}

/* ============================================
   SIDEBAR BUTTONS — NUCLEAR FIX
   ============================================ */

/* Target semua button di sidebar dengan multiple selectors */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stButton > button[kind="secondary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stButton"] > button,
[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"],
section[data-testid="stSidebar"] button {
    /* FORCE solid color, not rgba */
    background-color: #4C1D95 !important;
    background: #4C1D95 !important;
    background-image: none !important;
    color: #FFFFFF !important;
    border: 1px solid #7C3AED !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 10px 16px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    min-height: 42px !important;
    height: auto !important;
    width: 100% !important;
    margin-bottom: 4px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.15s ease !important;
}

/* Hover state */
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] button:hover {
    background-color: #6D28D9 !important;
    background: #6D28D9 !important;
    border-color: #A78BFA !important;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4) !important;
}

/* Active button (primary) — bright gradient */
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"],
section[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%) !important;
    background-color: #8B5CF6 !important;
    background-image: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5) !important;
}

/* Force ALL text inside buttons — level terdalam */
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button label,
[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] button *,
[data-testid="stSidebar"] button p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    background: transparent !important;
    background-color: transparent !important;
    font-weight: 600 !important;
    text-align: left !important;
    text-shadow: none !important;
    opacity: 1 !important;
}

/* ============================================
   SIDEBAR EXPANDER
   ============================================ */
[data-testid="stSidebar"] [data-testid="stExpander"],
[data-testid="stSidebar"] details {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] details > summary {
    background: #4C1D95 !important;
    background-color: #4C1D95 !important;
    background-image: none !important;
    color: #FFFFFF !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    border-left: 3px solid #A78BFA !important;
    cursor: pointer !important;
    margin-bottom: 6px !important;
    list-style: none !important;
}

[data-testid="stSidebar"] details > summary:hover {
    background: #6D28D9 !important;
    background-color: #6D28D9 !important;
    border-left-color: #EC4899 !important;
}

[data-testid="stSidebar"] details > summary *,
[data-testid="stSidebar"] details > summary p,
[data-testid="stSidebar"] details > summary span,
[data-testid="stSidebar"] details > summary svg {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
    background: transparent !important;
    font-weight: 700 !important;
}

/* Expander content — dark background */
[data-testid="stSidebar"] details > div,
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
    background: #1E1B4B !important;
    background-color: #1E1B4B !important;
    border-radius: 8px !important;
    padding: 8px !important;
    margin-bottom: 8px !important;
    border: none !important;
}

/* ============================================
   SIDEBAR INPUT / SELECT
   ============================================ */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #C4B5FD !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #C4B5FD !important;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stCaption {
    color: #A78BFA !important;
    font-size: 0.75rem !important;
}

[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid rgba(139, 92, 246, 0.3) !important;
    margin: 16px 0 !important;
}

/* ============================================
   MAIN CONTENT
   ============================================ */
h1 {
    color: #0F172A;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #1E1B4B 0%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
h2, h3 { color: #1E1B4B; font-weight: 700; }
h4, h5 { color: #334155; font-weight: 600; }

div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E9D5FF;
    padding: 20px 22px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.06);
    transition: all 0.25s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.12);
    border-color: #C4B5FD;
}
div[data-testid="stMetric"] label {
    color: #6D28D9 !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 1.8rem !important;
}

.main div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E9D5FF !important;
    border-radius: 14px !important;
    padding: 20px !important;
}

.main button[kind="primary"] {
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    font-weight: 700;
}
.main button[kind="secondary"] {
    background: #FFFFFF;
    color: #6D28D9;
    border: 1.5px solid #E9D5FF;
    border-radius: 10px;
    font-weight: 600;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

button[data-baseweb="tab"] {
    font-weight: 600;
    color: #6D28D9;
}
div[data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
    height: 3px;
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #E9D5FF;
}
div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(90deg, #F5F3FF 0%, #FAF5FF 100%);
    color: #4C1D95 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.7rem !important;
}

.main hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #E9D5FF 50%, transparent 100%);
    margin: 24px 0;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #F5F3FF; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #8B5CF6, #A855F7);
    border-radius: 4px;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}
/* ============================================
   SIDEBAR PREMIUM
   ============================================ */
[data-testid="stSidebar"] [data-testid="stExpander"] details > summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] details > summary span {
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    letter-spacing: 1.5px !important;
}

/* Sidebar header user profile */
.sb-user-card {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(167, 139, 250, 0.35);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    backdrop-filter: blur(8px);
}
.sb-avatar {
    width: 42px; height: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 800; font-size: 1.05rem;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
    flex-shrink: 0;
}
.sb-user-info { flex: 1; min-width: 0; }
.sb-user-name {
    color: #FFFFFF;
    font-weight: 700;
    font-size: 0.92rem;
    line-height: 1.2;
    margin-bottom: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.sb-user-role {
    color: #A78BFA;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Sidebar section header */
.sb-section-header {
    color: #A78BFA;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin: 18px 0 10px 4px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.25);
    position: relative;
}
.sb-section-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 40px; height: 2px;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
    border-radius: 2px;
}

/* Nav button active — indikator kiri */
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
    position: relative;
    padding-left: 20px !important;
}
[data-testid="stSidebar"] [data-testid="baseButton-primary"]::before {
    content: '';
    position: absolute;
    left: 4px; top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 60%;
    background: #FFFFFF;
    border-radius: 4px;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
}

/* Nav button hover — glow */
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {
    transform: translateX(3px);
    background: linear-gradient(90deg, #6D28D9 0%, #7C3AED 100%) !important;
    border-color: #A78BFA !important;
}

/* Expander summary — collapse animation smooth */
[data-testid="stSidebar"] details > summary {
    transition: all 0.2s ease !important;
}

</style>
"""

def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)