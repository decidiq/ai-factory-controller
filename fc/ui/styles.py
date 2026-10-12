"""Gaya tampilan Decidiq — Dark Premium Theme."""
import streamlit as st

CSS = """
<style>
/* ==================== FONT ==================== */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, button, input, select, textarea {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ==================== DESIGN TOKENS ==================== */
:root {
    --nav: #211846;
    --nav-text: #ded5f0;
    --nav-text-dim: #ac9dc9;
    --nav-hover: #ffffff12;
    --nav-active: #5834a2;
    --nav-active-bar: #89d84a;

    --night: #0d1026;
    --panel: #191d3b;
    --panel-2: #1a1d3d;
    --panel-3: #151933;
    --edge: #343858;
    --soft: #adb6d5;
    --white: #f5f6ff;
    --violet: #a489ff;
    --violet-deep: #7050d4;
    --cyan: #71d5e9;
    --green: #77edb4;
    --amber: #f7d578;
    --red: #ff9eaa;

    --radius: 15px;
    --radius-sm: 10px;
    --radius-xs: 8px;
    --gap: 20px;
    --pad-x: 38px;
    --max-width: 1550px;

    --primary-color: #7050d4;
    --background-color: #0d1026;
    --secondary-background-color: #191d3b;
    --text-color: #f5f6ff;
}

/* ==================== RESET ==================== */
* { box-sizing: border-box; }
.stApp {
    background: radial-gradient(ellipse at 75% -12%, #28214f 0%, transparent 38%),
                var(--night);
    color: var(--white);
}

/* ==================== LAYOUT ==================== */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: var(--pad-x) !important;
    padding-right: var(--pad-x) !important;
    max-width: var(--max-width) !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
.main .element-container { margin-bottom: 10px; }
.main [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
    gap: 12px !important;
}

/* ==================== SIDEBAR ==================== */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background: var(--nav) !important;
    background-color: var(--nav) !important;
    background-image: none !important;
    color: var(--nav-text) !important;
}
[data-testid="stSidebar"] {
    min-width: 240px !important;
    max-width: 240px !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #ffffff !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: var(--nav-text) !important;
}

/* ==================== NAV BUTTONS ==================== */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] button {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    color: var(--nav-text) !important;
    border: 0 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 9px 11px !important;
    border-radius: var(--radius-xs) !important;
    font-weight: 500 !important;
    font-size: 0.78rem !important;
    min-height: 34px !important;
    height: auto !important;
    width: 100% !important;
    margin-bottom: 2px !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] button:hover {
    background: var(--nav-hover) !important;
    background-color: var(--nav-hover) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"],
section[data-testid="stSidebar"] button[kind="primary"] {
    background: var(--nav-active) !important;
    background-color: var(--nav-active) !important;
    background-image: none !important;
    color: #ffffff !important;
    box-shadow: inset 3px 0 var(--nav-active-bar) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] button *,
[data-testid="stSidebar"] button p {
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
    background: transparent !important;
    background-color: transparent !important;
    font-weight: inherit !important;
    text-align: left !important;
    opacity: 1 !important;
}

/* ==================== SIDEBAR EXPANDER ==================== */
[data-testid="stSidebar"] [data-testid="stExpander"],
[data-testid="stSidebar"] details {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    margin: 0 0 6px 0 !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] details > summary {
    background: transparent !important;
    color: var(--nav-text-dim) !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 8px 4px !important;
    border: none !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    margin-bottom: 6px !important;
    list-style: none !important;
}
[data-testid="stSidebar"] details > summary:hover {
    color: #ffffff !important;
    border-bottom-color: rgba(255, 255, 255, 0.12) !important;
}
[data-testid="stSidebar"] details > summary *,
[data-testid="stSidebar"] details > summary p,
[data-testid="stSidebar"] details > summary span,
[data-testid="stSidebar"] details > summary svg {
    color: var(--nav-text-dim) !important;
    -webkit-text-fill-color: var(--nav-text-dim) !important;
    fill: var(--nav-text-dim) !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] details > summary:hover * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] details > div,
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 2px 0 4px 0 !important;
    margin-bottom: 4px !important;
}

/* ==================== SIDEBAR INPUTS ==================== */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background: #242748 !important;
    color: var(--white) !important;
    border: 1px solid #454766 !important;
    border-radius: var(--radius-xs) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #242748 !important;
    color: var(--white) !important;
    border: 1px solid #454766 !important;
    border-radius: var(--radius-xs) !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stCaption {
    color: var(--nav-text-dim) !important;
    font-size: 0.7rem !important;
}
[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
    margin: 12px 0 !important;
}

/* ==================== SIDEBAR USER CARD ==================== */
.sb-user-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-sm);
    padding: 12px 14px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.sb-avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 800; font-size: 0.95rem;
    flex-shrink: 0;
}
.sb-user-info { flex: 1; min-width: 0; }
.sb-user-name {
    color: #ffffff;
    font-weight: 700;
    font-size: 0.85rem;
    line-height: 1.2;
    margin-bottom: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.sb-user-role {
    color: var(--nav-text-dim);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ==================== HEADINGS ==================== */
h1, h2, h3, h4, h5 {
    color: var(--white) !important;
    font-weight: 800 !important;
}
h1 { letter-spacing: -0.045em !important; line-height: 1.15 !important; }
h2, h3 { letter-spacing: -0.025em !important; }

/* ==================== METRIC CARDS ==================== */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1a1d3d, #151933) !important;
    border: 1px solid var(--edge) !important;
    padding: 17px 18px !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13) !important;
    transition: transform 0.2s, border-color 0.2s !important;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: #8c79d7 !important;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45) !important;
}
div[data-testid="stMetric"] label {
    color: var(--soft) !important;
    font-weight: 700 !important;
    font-size: 0.66rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--white) !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
    letter-spacing: -0.04em !important;
}

/* ==================== CONTAINER / PANEL ==================== */
.main div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, #1a1d3d, #151933) !important;
    border: 1px solid var(--edge) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13) !important;
}

/* ==================== BUTTONS ==================== */
.main button[kind="primary"] {
    background: #7050d4 !important;
    color: #ffffff !important;
    border: 1px solid #8163ec !important;
    border-radius: var(--radius-xs) !important;
    font-weight: 700 !important;
}
.main button[kind="primary"]:hover {
    background: #8261ed !important;
    transform: translateY(-1px);
}
.main button[kind="secondary"] {
    background: #242748 !important;
    color: #f6f4ff !important;
    border: 1px solid #454766 !important;
    border-radius: var(--radius-xs) !important;
    font-weight: 700 !important;
}
.main button[kind="secondary"]:hover {
    background: #393367 !important;
}

/* ==================== ALERTS ==================== */
div[data-testid="stAlert"] {
    background: #232746 !important;
    border: 1px solid #3c4060 !important;
    border-radius: var(--radius-xs) !important;
    color: #f6f6ff !important;
}
div[data-testid="stAlert"] * {
    color: #f6f6ff !important;
}
div[data-testid="stAlert"][kind="success"] {
    background: #172d35 !important;
    border: 1px solid #276956 !important;
}
div[data-testid="stAlert"][kind="warning"] {
    background: #302b30 !important;
    border: 1px solid #756036 !important;
}
div[data-testid="stAlert"][kind="error"] {
    background: #35243a !important;
    border: 1px solid #794456 !important;
}
div[data-testid="stAlert"][kind="info"] {
    background: #242748 !important;
    border: 1px solid #3c4060 !important;
}

/* ==================== TABS ==================== */
button[data-baseweb="tab"] {
    font-weight: 600;
    color: var(--soft) !important;
    font-size: 0.85rem !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #ffffff !important;
}
div[data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, #a489ff 0%, #71d5e9 100%) !important;
    height: 3px !important;
}
div[data-baseweb="tab-border"] {
    background: var(--edge) !important;
}

/* ==================== DATAFRAME (MINIMAL) ==================== */
/* Note: Streamlit dataframe pakai canvas — biarkan Streamlit render sendiri.
   CSS hanya untuk border & radius. Background/text otomatis dari config.toml base=dark. */
div[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid var(--edge) !important;
}

/* ==================== INPUT / SELECT ==================== */
.main input[type="text"],
.main input[type="number"],
.main input[type="date"],
.main textarea {
    background: #242748 !important;
    color: var(--white) !important;
    border: 1px solid #454766 !important;
    border-radius: var(--radius-xs) !important;
}
.main [data-baseweb="select"] > div {
    background: #242748 !important;
    color: var(--white) !important;
    border: 1px solid #454766 !important;
    border-radius: var(--radius-xs) !important;
}
.main [role="listbox"] {
    background: #1a1d3d !important;
}
.main [role="option"] {
    background: #1a1d3d !important;
    color: #f5f6ff !important;
}
.main [role="option"]:hover {
    background: #2d3155 !important;
}
.main [data-testid="stRadio"] label p,
.main [data-testid="stCheckbox"] label p {
    color: #dce0f4 !important;
}
.main [data-testid="stSlider"] * {
    color: #dce0f4 !important;
}

/* ==================== GENERAL TEXT ==================== */
.main p, .main li, .main label {
    color: #dce0f4;
}
.main [data-testid="stCaptionContainer"] p,
.main .stCaption {
    color: var(--soft) !important;
    font-size: 0.78rem !important;
    line-height: 1.4 !important;
}

/* ==================== SPACING ==================== */
.main [data-testid="stHorizontalBlock"] {
    gap: 14px !important;
}
.main [data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
}
.main [data-testid="column"] > div:first-child {
    flex: 1 !important;
}
.main [data-testid="stPlotlyChart"] {
    min-height: 300px;
}
.section-gap { height: 24px; width: 100%; }

/* ==================== EXPANDER (MAIN) ==================== */
.main [data-testid="stExpander"] {
    background: var(--panel-2) !important;
    border: 1px solid var(--edge) !important;
    border-radius: var(--radius-sm) !important;
    margin-bottom: 12px !important;
}
.main [data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: var(--white) !important;
    padding: 12px 16px !important;
}
.main [data-testid="stExpander"] summary:hover {
    background: #242748 !important;
}

/* ==================== HEADER BAR ==================== */
[data-testid="stHeader"],
header[data-testid="stHeader"] {
    background: transparent !important;
    background-color: transparent !important;
    backdrop-filter: none !important;
}
[data-testid="stHeader"] * { color: #dce0f4 !important; }
.stApp > header { background: transparent !important; }
[data-testid="stToolbar"] { background: transparent !important; }
[data-testid="stToolbar"] button {
    background: transparent !important;
    color: #adb6d5 !important;
}
[data-testid="stToolbar"] button:hover {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #ffffff !important;
}
[data-testid="stAppViewContainer"] > .main { background: transparent !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ==================== SCROLLBAR ==================== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #151933; }
::-webkit-scrollbar-thumb {
    background: #3c4060;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: #565b81; }

/* ==================== HIDE MENU ==================== */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* ============================================
   SIDEBAR — PRECISION SPACING (rapat & konsisten)
   ============================================ */

/* Sidebar padding lebih compact */
[data-testid="stSidebar"] > div:first-child {
    padding: 12px 10px !important;
}

/* Kurangi gap antar elemen di sidebar */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 6px !important;
}
[data-testid="stSidebar"] .element-container {
    margin-bottom: 4px !important;
}

/* User card lebih compact */
.sb-user-card {
    padding: 10px 12px !important;
    margin-bottom: 8px !important;
    gap: 10px !important;
}
.sb-avatar {
    width: 34px !important;
    height: 34px !important;
    font-size: 0.85rem !important;
}
.sb-user-name {
    font-size: 0.8rem !important;
}
.sb-user-role {
    font-size: 0.6rem !important;
}

/* Logout button — compact */
[data-testid="stSidebar"] .stButton > button {
    min-height: 30px !important;
    padding: 6px 10px !important;
    font-size: 0.75rem !important;
    margin-bottom: 1px !important;
}

/* Markdown text (Navigation, dll) — lebih kecil & rapat */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
    font-size: 0.72rem !important;
    line-height: 1.3 !important;
    margin: 2px 0 !important;
}

/* Section header di sidebar (markdown ### atau ####) */
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    font-size: 0.72rem !important;
    margin: 8px 0 4px 0 !important;
    padding: 4px 0 !important;
}

/* Expander (section group) — rapat */
[data-testid="stSidebar"] details {
    margin: 0 0 2px 0 !important;
}
[data-testid="stSidebar"] details > summary {
    padding: 6px 8px !important;
    min-height: 26px !important;
    font-size: 0.62rem !important;
    letter-spacing: 1.2px !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] details > div {
    padding: 2px 0 !important;
    margin-bottom: 2px !important;
}

/* Divider HR — rapat */
[data-testid="stSidebar"] hr {
    margin: 8px 0 !important;
}

/* Radio button (Path File Excel, dll) — compact */
[data-testid="stSidebar"] [data-testid="stRadio"] {
    margin: 2px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 4px 0 !important;
    font-size: 0.75rem !important;
    min-height: 24px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.75rem !important;
    line-height: 1.2 !important;
}

/* Text input (Path file) */
[data-testid="stSidebar"] input[type="text"] {
    min-height: 32px !important;
    font-size: 0.75rem !important;
    padding: 6px 10px !important;
}

/* Caption kecil (Path file label, dll) */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    font-size: 0.68rem !important;
    margin: 2px 0 !important;
}

/* Spacer di antara grup — kurangi */
[data-testid="stSidebar"] .stMarkdown {
    margin-bottom: 2px !important;
}

/* File uploader (Unggah Excel) */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    margin: 4px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] label {
    font-size: 0.72rem !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    padding: 8px !important;
    min-height: 60px !important;
}
/* ============================================
   GLOBAL DARK OVERRIDE — semua custom card class
   ============================================ */

/* Semua class yang berakhir dengan "-glass" → dark */
[class$="-glass"] {
    background: linear-gradient(145deg, #1a1d3d, #151933) !important;
    border: 1px solid #343858 !important;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13) !important;
}
[class$="-glass"]::before {
    background: linear-gradient(90deg, var(--accent, #a489ff) 0%, #71d5e9 100%) !important;
}
[class$="-glass-label"] {
    color: #b8bedb !important;
    font-weight: 600 !important;
    font-size: 0.62rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[class$="-glass-value"] {
    color: #ffffff !important;
    font-weight: 800 !important;
}
[class$="-glass-note"] {
    color: #8793bc !important;
}
[class$="-glass-delta"] {
    font-weight: 700 !important;
}

/* Recommendation Card */
.rec-card {
    background: #1b1e3e !important;
    border: 1px solid #343858 !important;
    border-left-width: 5px !important;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13) !important;
}
.rec-title {
    color: #f5f6ff !important;
}
.rec-meta {
    color: #c4aaff !important;
}
.rec-context {
    background: #242748 !important;
    color: #dce0f4 !important;
}
.rec-context strong {
    color: #a489ff !important;
}
.rec-step {
    background: linear-gradient(90deg, #242748 0%, #1a1d3d 100%) !important;
    border-left-color: #a489ff !important;
    color: #dce0f4 !important;
}
.rec-step-num {
    color: #c4aaff !important;
}
.rec-badge {
    /* Warna via inline style — biarkan */
}

/* Generic metric-card pattern */
.metric-card {
    background: linear-gradient(145deg, #1a1d3d, #151933) !important;
    border: 1px solid #343858 !important;
}

/* Executive report inline override */
.exec-summary-box {
    background: #191d3b !important;
    color: #dce0f4 !important;
}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)