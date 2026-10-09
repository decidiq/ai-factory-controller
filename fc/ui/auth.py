"""Login page Decidiq - Split-Screen Premium UI."""
from datetime import datetime

import streamlit as st

from .. import audit

ROLES = ["Director / GM", "Factory Manager / Plant Controller"]

# ==================== MENU STRUCTURE (NESTED) ====================

ROLE_MENUS = {
    "Director / GM": {
        "📊 OVERVIEW": ["Dashboard", "Executive Report", "Kualitas Data"],
        "💰 COST INTELLIGENCE": [
            "Cost DNA", "Standard vs Actual", "Cost Analysis",
            "Multi-Plant & Cost Allocation",
        ],
        "🎯 DECISION SUPPORT": ["Recommendations", "Memory", "AI Copilot"],
        "⚙️ SYSTEM": ["Audit Trail", "Settings"],
    },
    "Factory Manager / Plant Controller": {
        "📊 OVERVIEW": ["Dashboard", "Executive Report", "Kualitas Data"],
        "💰 COST INTELLIGENCE": [
            "Cost DNA", "Standard vs Actual", "Cost Analysis",
            "Manufacturing Variance", "What-If Simulator",
            "Multi-Plant & Cost Allocation",
        ],
        "🏭 OPERATIONS": [
            "Production Analysis", "Predictive Analytics",
            "Inventory Analysis", "Risk Register",
        ],
        "🎯 DECISION SUPPORT": ["Recommendations", "Memory", "AI Copilot"],
        "⚙️ SYSTEM": ["Audit Trail", "Settings"],
        "🚧 COMING SOON": [
            "Multi-Agent Collaboration", "AI Factory OS (Phase 5)",
        ],
    },
}

# ==================== ICON MAP ====================
ICON_MAP = {
    "Dashboard": "📊", "Executive Report": "📋", "Kualitas Data": "✅",
    "Cost DNA": "🧬", "Standard vs Actual": "⚖️", "Cost Analysis": "💰",
    "Multi-Plant & Cost Allocation": "🏭", "Manufacturing Variance": "📉",
    "What-If Simulator": "🎯", "Production Analysis": "⚙️",
    "Predictive Analytics": "📈", "Inventory Analysis": "📦",
    "Risk Register": "⚠️", "Recommendations": "💡", "Memory": "🧠",
    "AI Copilot": "🤖", "Audit Trail": "📜", "Settings": "⚙️",
    "Multi-Agent Collaboration": "🤝", "AI Factory OS (Phase 5)": "🏗️",
}


def _log_local(user: str, action: str) -> None:
    st.session_state.setdefault("activity_logs", []).insert(
        0, {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "User": user, "Action": action})


def _is_session_valid() -> bool:
    return (st.session_state.get("authenticated") is True
            and "role" in st.session_state
            and st.session_state.get("role") in ROLE_MENUS)


# ==================== LOGIN PAGE CSS ====================
LOGIN_CSS = """
<style>
/* Full screen — hilangkan padding Streamlit */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
}

/* Split screen layout */
div[data-testid="stHorizontalBlock"] {
    min-height: 100vh;
    gap: 0 !important;
}

/* Sisi Kiri — Hero */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #4C1D95 100%);
    padding: 60px 50px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    text-align: left;
    color: white;
    position: relative;
    overflow: hidden;
}

/* Ornamen lingkaran di background hero */
div[data-testid="stHorizontalBlock"] > div:nth-child(1)::before {
    content: '';
    position: absolute;
    top: -100px; right: -100px;
    width: 400px; height: 400px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.35) 0%, transparent 70%);
    pointer-events: none;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1)::after {
    content: '';
    position: absolute;
    bottom: -120px; left: -80px;
    width: 350px; height: 350px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(236, 72, 153, 0.25) 0%, transparent 70%);
    pointer-events: none;
}

/* Sisi Kanan — Form */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    background: #FAFAFA;
    padding: 60px 40px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

/* Kartu Login */
div[data-testid="stVerticalBlockBorderWrapper"] {
    width: 100%;
    max-width: 420px;
    box-shadow: 0 20px 50px rgba(139, 92, 246, 0.12) !important;
    border: 1px solid #E9D5FF !important;
    border-radius: 20px !important;
    padding: 32px !important;
    background: #FFFFFF !important;
    position: relative;
    overflow: hidden;
}
div[data-testid="stVerticalBlockBorderWrapper"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
}

/* Hero Content */
.hero-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
}
.hero-logo {
    width: 52px; height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.5);
}
.hero-name {
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: -0.5px;
    color: #FFFFFF;
    line-height: 1;
}
.hero-name-sub {
    font-size: 0.7rem;
    color: #A78BFA;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 4px;
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: -1.5px;
    line-height: 1.15;
    margin-bottom: 14px;
    color: #FFFFFF;
    position: relative;
    z-index: 1;
}
.hero-title-accent {
    background: linear-gradient(90deg, #A78BFA 0%, #EC4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-tagline {
    font-size: 1rem;
    color: #C4B5FD;
    font-weight: 600;
    margin-bottom: 36px;
    letter-spacing: 0.3px;
    position: relative;
    z-index: 1;
}

/* Feature highlights */
.hero-features {
    display: flex;
    flex-direction: column;
    gap: 16px;
    position: relative;
    z-index: 1;
}
.hero-feature {
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.hero-feature-icon {
    width: 32px; height: 32px;
    border-radius: 8px;
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    flex-shrink: 0;
}
.hero-feature-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 2px;
}
.hero-feature-desc {
    font-size: 0.76rem;
    color: #94A3B8;
    line-height: 1.4;
}

/* Footer versi */
.hero-footer {
    position: absolute;
    bottom: 24px;
    left: 50px;
    font-size: 0.7rem;
    color: #64748B;
    letter-spacing: 0.5px;
    z-index: 1;
}

/* Form header */
.form-header {
    text-align: center;
    margin-bottom: 24px;
}
.form-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.form-sub {
    font-size: 0.85rem;
    color: #64748B;
}

/* Login footer caption */
.login-footer {
    text-align: center;
    color: #94A3B8;
    font-size: 0.75rem;
    margin-top: 14px;
    line-height: 1.6;
}
/* ============================================
   FIX: SELECTBOX DI SIDEBAR
   ============================================ */
/* Semua elemen di dalam select — paksa teks gelap */
[data-testid="stSidebar"] [data-baseweb="select"],
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] p,
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] [role="button"],
[data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 600 !important;
}

/* Background & border selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #C4B5FD !important;
    border-radius: 8px !important;
}

/* Dropdown list (saat dibuka) */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background: #FFFFFF !important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] li {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    background: #FFFFFF !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover {
    background: #F5F3FF !important;
}

/* Label selectbox ("Pilih Plant", "Pilih Lini Produksi") */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #E9D5FF !important;
    -webkit-text-fill-color: #E9D5FF !important;
}

/* Subheader & judul filter di sidebar */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

</style>
"""

def require_login() -> None:
    if _is_session_valid():
        return

    if st.session_state.get("authenticated"):
        st.session_state.clear()

    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # ==================== RENDER SPLIT SCREEN ====================
    col1, col2 = st.columns([1.15, 1])

    with col1:
        st.markdown("""
        <div class="hero-brand">
            <div class="hero-logo">🧠</div>
            <div>
                <div class="hero-name">Decidiq</div>
                <div class="hero-name-sub">Decision Intelligence</div>
            </div>
        </div>

        <div class="hero-title">
            Smart Decisions,<br>
            <span class="hero-title-accent">Delivered.</span>
        </div>

        <div class="hero-tagline">
            Platform AI yang mengubah data kompleks menjadi keputusan bisnis yang cepat dan akurat.
        </div>

        <div class="hero-features">
            <div class="hero-feature">
                <div class="hero-feature-icon">📊</div>
                <div>
                    <div class="hero-feature-title">Real-time Analytics</div>
                    <div class="hero-feature-desc">Monitor KPI operasional & finansial dalam satu dashboard.</div>
                </div>
            </div>
            <div class="hero-feature">
                <div class="hero-feature-icon">🧬</div>
                <div>
                    <div class="hero-feature-title">Cost DNA Engine</div>
                    <div class="hero-feature-desc">Urai variance biaya: harga, volume, mix, dan efisiensi.</div>
                </div>
            </div>
            <div class="hero-feature">
                <div class="hero-feature-icon">🤖</div>
                <div>
                    <div class="hero-feature-title">AI Copilot</div>
                    <div class="hero-feature-desc">Tanya data pabrik dalam bahasa natural, dapat jawaban instan.</div>
                </div>
            </div>
        </div>

        <div class="hero-footer">© 2026 Decidiq · v1.0</div>
        """, unsafe_allow_html=True)

    with col2:
        with st.container(border=True):
            st.markdown("""
            <div class="form-header">
                <div class="form-title">🔐 Welcome Back</div>
                <div class="form-sub">Sign in to your Decidiq account</div>
            </div>
            """, unsafe_allow_html=True)

            user = st.text_input("Username", placeholder="your.username",
                                  key="login_user")
            st.text_input("Password", type="password",
                          placeholder="••••••••",
                          help="Belum diverifikasi (temporary login)",
                          key="login_pass")
            role = st.selectbox("Pilih Role", ROLES, key="login_role")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In →", type="primary",
                         use_container_width=True, key="login_btn"):
                username = (user or "").strip()
                if not username:
                    st.error("Masukkan username Anda.")
                elif role not in ROLE_MENUS:
                    st.error("Role tidak valid.")
                else:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = role

                    _log_local(username, f"Login [{role}]")
                    try:
                        audit.log_login(username, role)
                    except Exception:
                        pass

                    st.rerun()

        st.markdown("""
        <div class="login-footer">
            ⚠️ Login sementara — belum verifikasi password<br>
            Demo: username apa saja · role pilih bebas
        </div>
        """, unsafe_allow_html=True)

    st.stop()


def logout() -> None:
    username = st.session_state.get("username", "")
    _log_local(username, "Logout")
    try:
        audit.log_logout(username)
    except Exception:
        pass
    st.session_state.clear()
    st.rerun()