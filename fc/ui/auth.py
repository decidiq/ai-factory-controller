"""LOGIN SEMENTARA - tanpa verifikasi password.

PERHATIAN: modul ini BELUM AMAN (password tidak diperiksa, role dipilih sendiri).
Sesuai keputusan, bagian login & hak akses diperbarui terakhir (BRD bagian 4 dan 13).
Jangan dipakai untuk data nyata di luar lingkungan uji sampai diganti.
"""
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
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("## 🔐 Enterprise Login")
        st.caption("⚠️ Login sementara - belum memverifikasi password. Pilih username & role apa saja.")
        user = st.text_input("Username", placeholder="mis. admin")
        st.text_input("Password", type="password",
                      help="Belum diverifikasi - isi apa saja atau kosongkan")
        role = st.selectbox("Pilih Role Jabatan", ROLES)
        if st.button("Masuk ke Sistem", type="primary", use_container_width=True):
            if user.strip():
                username = user.strip()
                st.session_state.update(
                    authenticated=True, username=username, role=role)
                _log_local(username, f"Login [{role}]")
                audit.log_login(username, role)
                st.rerun()
            else:
                st.error("Mohon masukkan username Anda.")
    st.stop()


def logout() -> None:
    username = st.session_state.get("username", "")
    _log_local(username, "Logout")
    audit.log_logout(username)
    for k in ("authenticated", "username", "role"):
        st.session_state.pop(k, None)
    st.rerun()