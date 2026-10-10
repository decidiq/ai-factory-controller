"""Login page Decidiq - Split-Screen Premium UI."""
import base64
import os
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


# ==================== DEVELOPER INFO ====================
DEV_NAME = "Randi Meiza"
DEV_ROLE = "Lead Developer"
DEV_LINKEDIN = "https://www.linkedin.com/in/randi-meiza-93a67293"
DEV_PHOTO_PATH = "assets/developer.jpg"


def _get_developer_avatar_html() -> str:
    """Ambil foto developer, convert ke base64. Fallback ke inisial."""
    # Coba baca foto
    if os.path.exists(DEV_PHOTO_PATH):
        try:
            with open(DEV_PHOTO_PATH, "rb") as f:
                img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            ext = os.path.splitext(DEV_PHOTO_PATH)[1].lower().lstrip(".")
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            return (
                f'<div class="hero-dev-avatar-photo" '
                f'style="background-image: url(\'data:{mime};base64,{b64}\');">'
                f'</div>'
            )
        except Exception:
            pass

    # Fallback: inisial
    initial = DEV_NAME.strip()[0].upper() if DEV_NAME else "D"
    return f'<div class="hero-dev-avatar">{initial}</div>'


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
    padding: 40px 50px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: flex-start;
    text-align: left;
    color: white;
    position: relative;
    overflow: hidden;
}

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
    margin-bottom: 24px;
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
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -1.2px;
    line-height: 1.15;
    margin-bottom: 12px;
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
    font-size: 0.9rem;
    color: #C4B5FD;
    font-weight: 500;
    margin-bottom: 24px;
    letter-spacing: 0.2px;
    line-height: 1.5;
    position: relative;
    z-index: 1;
}

/* Feature highlights */
.hero-features {
    display: flex;
    flex-direction: column;
    gap: 9px;
    position: relative;
    z-index: 1;
    margin-bottom: 16px;
}
.hero-feature {
    display: flex;
    align-items: flex-start;
    gap: 10px;
}
.hero-feature-icon {
    width: 26px; height: 26px;
    border-radius: 7px;
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
}
.hero-feature-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 2px;
}
.hero-feature-desc {
    font-size: 0.68rem;
    color: #94A3B8;
    line-height: 1.35;
}

/* Divider */
.hero-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(139, 92, 246, 0.4) 50%, transparent 100%);
    margin: 18px 0;
    position: relative;
    z-index: 1;
}

/* About Section */
.hero-about-label {
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #A78BFA;
    text-transform: uppercase;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.hero-about-text {
    font-size: 0.82rem;
    color: #C4B5FD;
    line-height: 1.6;
    position: relative;
    z-index: 1;
}
.hero-about-text strong { color: #FBBF24; }

/* Developer Section */
.hero-dev-card {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(167, 139, 250, 0.3);
    border-radius: 12px;
    padding: 12px 16px;
    margin-top: 8px;
    position: relative;
    z-index: 1;
    transition: all 0.2s ease;
}
.hero-dev-card:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(167, 139, 250, 0.5);
}
.hero-dev-avatar {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 1.15rem;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
    flex-shrink: 0;
}
.hero-dev-avatar-photo {
    width: 48px; height: 48px;
    border-radius: 50%;
    background-size: cover;
    background-position: center;
    border: 2px solid #8B5CF6;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
    flex-shrink: 0;
}
.hero-dev-info { flex: 1; min-width: 0; }
.hero-dev-role {
    font-size: 0.62rem;
    color: #A78BFA;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.hero-dev-name {
    font-size: 0.95rem;
    color: #FFFFFF;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 5px;
}
.hero-dev-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
    color: #FFFFFF;
    background: linear-gradient(135deg, #0A66C2 0%, #0077B5 100%);
    padding: 4px 10px;
    border-radius: 6px;
    text-decoration: none;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(10, 102, 194, 0.4);
}
.hero-dev-link:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(10, 102, 194, 0.6);
    color: #FFFFFF;
}

/* Footer versi */
.hero-footer {
    font-size: 0.7rem;
    color: #64748B;
    letter-spacing: 0.5px;
    margin-top: 16px;
    position: relative;
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
        avatar_html = _get_developer_avatar_html()

        st.markdown(f"""
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

        <div class="hero-divider"></div>

        <div class="hero-about-label">👨‍💻 Developed By</div>
        <div class="hero-dev-card">
            {avatar_html}
            <div class="hero-dev-info">
                <div class="hero-dev-role">{DEV_ROLE}</div>
                <div class="hero-dev-name">{DEV_NAME}</div>
                <a class="hero-dev-link" href="{DEV_LINKEDIN}" target="_blank" rel="noopener noreferrer">
                    💼 LinkedIn Profile →
                </a>
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