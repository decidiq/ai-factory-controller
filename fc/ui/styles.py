"""Gaya tampilan Decidiq — Modern Gradient Theme (Linear-inspired)."""
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

/* === SIDEBAR === */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E1B4B 0%, #312E81 100%);
    color: #E9D5FF;
    min-width: 260px !important;
    max-width: 260px !important;
}
[data-testid="stSidebar"] > div:first-child {
    background: transparent;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-weight: 700;
    letter-spacing: -0.3px;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #C4B5FD !important;
}
[data-testid="stSidebar"] .stRadio > label {
    color: #E9D5FF !important;
    font-weight: 500;
    font-size: 0.9rem;
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    padding: 8px 12px;
    border-radius: 8px;
    transition: all 0.2s ease;
    color: #E9D5FF !important;
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
    background: rgba(139, 92, 246, 0.15);
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, #8B5CF6 0%, #A855F7 100%);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) p,
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) span {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(139, 92, 246, 0.2);
    color: #FFFFFF;
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(139, 92, 246, 0.35);
    border-color: #8B5CF6;
}

/* === TYPOGRAPHY === */
h1 {
    color: #0F172A;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #1E1B4B 0%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
h2, h3 {
    color: #1E1B4B;
    font-weight: 700;
    letter-spacing: -0.5px;
}
h4, h5 { color: #334155; font-weight: 600; }

/* === METRIC CARDS === */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E9D5FF;
    padding: 20px 22px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.06), 0 1px 3px rgba(0,0,0,0.03);
    transition: all 0.25s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.12), 0 2px 6px rgba(0,0,0,0.04);
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
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-weight: 600;
    font-size: 0.85rem;
}

/* === CONTAINER / CARDS === */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E9D5FF !important;
    border-radius: 14px !important;
    padding: 20px !important;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.05);
}
div[data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid #E9D5FF;
    border-radius: 12px;
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #4C1D95;
}

/* === ALERTS === */
div[data-testid="stAlert"] {
    border-radius: 12px;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    padding: 16px 18px;
}
div[data-testid="stAlert"][data-baseweb="notification"] {
    border-left: 4px solid;
}

/* === BUTTONS === */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    padding: 10px 20px;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    transition: all 0.2s ease;
    letter-spacing: 0.2px;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF;
    color: #6D28D9;
    border: 1.5px solid #E9D5FF;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover {
    background: #F5F3FF;
    border-color: #8B5CF6;
}

/* === INPUT === */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stDateInput"] input {
    border-radius: 10px;
    border: 1.5px solid #E9D5FF;
    background: #FFFFFF;
    font-weight: 500;
    transition: border-color 0.2s ease;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: #8B5CF6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

/* === TABS === */
button[data-baseweb="tab"] {
    font-weight: 600;
    color: #6D28D9;
    border-radius: 8px 8px 0 0;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #4C1D95;
    background: linear-gradient(180deg, transparent 0%, rgba(139, 92, 246, 0.1) 100%);
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
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.05);
}
div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(90deg, #F5F3FF 0%, #FAF5FF 100%);
    color: #4C1D95 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.7rem !important;
    letter-spacing: 0.5px;
}

/* === DIVIDER === */
hr {
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
::-webkit-scrollbar-thumb:hover { background: #7C3AED; }

/* === CAPTION === */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #64748B;
    font-size: 0.8rem;
    font-weight: 500;
}

/* === PLOTLY === */
.js-plotly-plot .plotly .modebar {
    background: rgba(255, 255, 255, 0.9) !important;
    border-radius: 8px;
}

/* === SPECIAL: BRAND LOGO === */
.decidiq-logo {
    font-weight: 900;
    font-size: 1.4rem;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* === HIDE STREAMLIT MENU === */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* === MAIN CONTAINER SPACING === */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)