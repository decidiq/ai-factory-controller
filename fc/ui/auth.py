"""Login page Decidiq - tanpa verifikasi password (temporary)."""
from datetime import datetime

import streamlit as st

from .. import audit

ROLES = ["Director / GM", "Factory Manager / Plant Controller"]

ROLE_MENUS = {
    "Director / GM": [
        "Dashboard",
        "Kualitas Data",
        "Audit Trail",
        "Cost DNA",
        "What-If Simulator",
        "Recommendations",
        "Memory",
        "Cost Analysis",
        "Multi-Plant & Cost Allocation",
        "Executive Report",
        "AI Copilot",
        "Settings",
    ],
    "Factory Manager / Plant Controller": [
        "Dashboard",
        "Kualitas Data",
        "Audit Trail",
        "Production Analysis",
        "Predictive Analytics",
        "Cost DNA",
        "What-If Simulator",
        "Recommendations",
        "Memory",
        "Cost Analysis",
        "Multi-Plant & Cost Allocation",
        "Manufacturing Variance",
        "Inventory Analysis",
        "Risk Register",
        "Multi-Agent Collaboration",
        "AI Factory OS (Phase 5)",
        "Executive Report",
        "AI Copilot",
        "Settings",
    ],
}


def _log_local(user: str, action: str) -> None:
    st.session_state.setdefault("activity_logs", []).insert(
        0, {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "User": user, "Action": action})


def _is_session_valid() -> bool:
    """Session valid kalau authenticated=True DAN role ada di session."""
    return (st.session_state.get("authenticated") is True
            and "role" in st.session_state
            and st.session_state.get("role") in ROLE_MENUS)


def require_login() -> None:
    # Kalau session valid → lanjut
    if _is_session_valid():
        return

    # Kalau session corrupt → clear
    if st.session_state.get("authenticated"):
        st.session_state.clear()

    # Custom CSS
    st.markdown("""
    <style>
    .login-hero {
        text-align: center;
        padding: 40px 20px 20px 20px;
    }
    .login-brand {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -2px;
        background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
    }
    .login-tagline {
        font-size: 1rem;
        color: #6D28D9;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .login-sub {
        font-size: 0.85rem;
        color: #94A3B8;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])

    with mid:
        st.markdown("""
        <div class="login-hero">
            <div class="login-brand">Decidiq</div>
            <div class="login-tagline">Smart Decisions, Delivered.</div>
            <div class="login-sub">Decision Intelligence Platform</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### 🔐 Welcome Back")
            st.caption("Sign in to your Decidiq account")

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
                    # Set session LENGKAP
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = role

                    _log_local(username, f"Login [{role}]")
                    try:
                        audit.log_login(username, role)
                    except Exception:
                        pass

                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("⚠️ Login sementara — belum verifikasi password")
        st.caption("Demo: username apa saja · role pilih bebas")

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