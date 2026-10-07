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


def require_login() -> None:
    if st.session_state.get("authenticated"):
        return

    # Custom CSS untuk login page
    st.markdown("""
    <style>
    /* Login container */
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
    .login-card {
        background: #FFFFFF;
        border: 1px solid #E9D5FF;
        border-radius: 18px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(139, 92, 246, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])

    with mid:
        # Brand hero
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
                if user.strip():
                    username = user.strip()
                    st.session_state.update(
                        authenticated=True, username=username, role=role)
                    _log_local(username, f"Login [{role}]")
                    audit.log_login(username, role)
                    st.rerun()
                else:
                    st.error("Masukkan username Anda.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("⚠️ Login sementara — belum verifikasi password")
        st.caption("Demo: username apa saja · role pilih bebas")


def logout() -> None:
    username = st.session_state.get("username", "")
    _log_local(username, "Logout")
    audit.log_logout(username)
    for k in ("authenticated", "username", "role"):
        st.session_state.pop(k, None)
    st.rerun()