"""Gaya tampilan Decidiq — Modern Gradient Theme."""
import streamlit as st

CSS = """
<style>
/* === RESET === */
* { box-sizing: border-box; }
.stApp {
    background: #FAFAFA;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #0F172A;
}

/* ============================================
   SIDEBAR — AGRESSIVE STYLING
   ============================================ */

/* Force sidebar background */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div {
    background: linear-gradient(180deg, #1E1B4B 0%, #312E81 100%) !important;
    color: #E9D5FF !important;
}

[data-testid="stSidebar"] {
    min-width: 280px !important;
    max-width: 280px !important;
}

/* Sidebar text colors */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p {
    color: #FFFFFF !important;
}

/* ============================================
   SIDEBAR BUTTONS — FORCE COLORS
   ============================================ */

/* Base button styling - all buttons in sidebar */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] .stButton button {
    background-color: rgba(139, 92, 246, 0.20) !important;
    color: #E9D5FF !important;
    border: 1px solid rgba(139, 92, 246, 0.35) !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 8px 14px !important;
    border-radius: 8px !important;
    margin-bottom: 3px !important;
    transition: all 0.15s ease !important;
    min-height: 36px !important;
    height: auto !important;
}

/* Force text inside button — semua tag */
[data-testid="stSidebar"] button *,
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div,
[data-testid="stSidebar"] button label {
    color: #E9D5FF !important;
    text-align: left !important;
    font-weight: 500 !important;
}

/* Hover state */
[data-testid="stSidebar"] button:hover {
    background-color: rgba(139, 92, 246, 0.40) !important;
    border-color: #8B5CF6 !important;
}
[data-testid="stSidebar"] button:hover *,
[data-testid="stSidebar"] button:hover p,
[data-testid="stSidebar"] button:hover span,
[data-testid="stSidebar"] button:hover div {
    color: #FFFFFF !important;
}

/* Active button (primary) — bright purple gradient */
[data-testid="stSidebar"] button[kind="primary"],
section[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5) !important;
}
[data-testid="stSidebar"] button[kind="primary"] *,
[data-testid="stSidebar"] button[kind="primary"] p,
[data-testid="stSidebar"] button[kind="primary"] span,
[data-testid="stSidebar"] button[kind="primary"] div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ============================================
   SIDEBAR EXPANDER (KATEGORI MENU)
   ============================================ */

[data-testid="stSidebar"] [data-testid="stExpander"],
[data-testid="stSidebar"] details {
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] details > summary,
[data-testid="stSidebar"] details > summary {
    background-color: rgba(139, 92, 246, 0.25) !important;
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
    transition: all 0.15s ease !important;
    list-style: none !important;
}

[data-testid="stSidebar"] details > summary:hover {
    background-color: rgba(139, 92, 246, 0.45) !important;
    border-left-color: #EC4899 !important;
}

/* Force summary text — multi-layer */
[data-testid="stSidebar"] details > summary *,
[data-testid="stSidebar"] details > summary p,
[data-testid="stSidebar"] details > summary span,
[data-testid="stSidebar"] details > summary div,
[data-testid="stSidebar"] details > summary svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Expander content — background gelap agar tidak putih */
[data-testid="stSidebar"] details > div,
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
    background-color: rgba(15, 23, 42, 0.4) !important;
    border-radius: 8px !important;
    padding: 8px !important;
    margin-bottom: 8px !important;
}

/* ============================================
   SIDEBAR INPUT / SELECT
   ============================================ */

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #C4B5FD !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #E9D5FF !important;
    font-weight: 500 !important;
}

/* Sidebar caption kecil */
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #A78BFA !important;
    font-size: 0.75rem !important;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid rgba(139, 92, 246, 0.3) !important;
    margin: 16px 0 !important;
}

/* ============================================
   MAIN CONTENT (di luar sidebar)
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
h2, h3 { color: #1E1B4B; font-weight: 700; letter-spacing: -0.5px; }
h4, h5 { color: #334155; font-weight: 600; }

/* === METRIC CARDS === */
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
    letter-spacing: 0.6px;
    text-transform: uppercase;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 1.8rem !important;
    letter-spacing: -0.5px;
}

/* === CONTAINER / CARDS (main content) === */
.main div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E9D5FF !important;
    border-radius: 14px !important;
    padding: 20px !important;
}

/* === MAIN BUTTONS === */
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

/* === ALERTS === */
div[data-testid="stAlert"] {
    border-radius: 12px;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* === TABS === */
button[data-baseweb="tab"] {
    font-weight: 600;
    color: #6D28D9;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #4C1D95;
}
div[data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
    height: 3px;
    border-radius: 2px;
}

/* === DATAFRAME === */
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

/* === DIVIDER === */
.main hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #E9D5FF 50%, transparent 100%);
    margin: 24px 0;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #F5F3FF; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #8B5CF6, #A855F7);
    border-radius: 4px;
}

/* === HIDE STREAMLIT MENU === */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* === MAIN CONTAINER === */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)