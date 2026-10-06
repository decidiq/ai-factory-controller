"""AI Copilot dasar - berbasis kata kunci (BRD 8)."""
import streamlit as st

from ..kpi import Scope, summarize
from ..pipeline import Dataset


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🤖 AI Copilot (Dasar)")
    st.caption("Asisten berbasis kata kunci. Belum memakai LLM (lihat roadmap Tahap 3 & 5).")

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [{
            "role": "assistant",
            "content": "Halo! Saya AI Copilot **dasar**. Saya hanya menjawab dengan data tersedia. "
                       "Coba: *output*, *yield*, *scrap*, *oee*, *cogm*, *cost/kg*.",
        }]

    for m in st.session_state.copilot_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Tanyakan tentang data produksi...")
    if not prompt:
        return

    st.session_state.copilot_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = _answer(ds, scope, prompt.lower())
    st.session_state.copilot_messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)


def _answer(ds, scope, q):
    s = summarize(ds, scope)

    def _v(kpi, label, fmt="{:,.2f}"):
        return (f"**{label}**: {fmt.format(kpi.value)}" if kpi.available
                else f"**{label}**: data tidak tersedia ({kpi.note})")

    if any(k in q for k in ("output", "produksi")):
        return _v(s.output_kg, "Total Output", "{:,.0f} Kg")
    if "yield" in q:
        return _v(s.yield_pct, "Yield", "{:.2f}%")
    if "scrap" in q:
        return _v(s.scrap_pct, "Scrap", "{:.2f}%")
    if "oee" in q:
        return _v(s.oee.oee, "OEE", "{:.2f}%")
    if "cogm" in q or "total biaya" in q:
        return _v(s.cogm, "COGM", "Rp {:,.0f}")
    if "cost/kg" in q or "cost per kg" in q:
        return _v(s.cost_per_kg, "Cost/Kg", "Rp {:,.0f}")

    return ("Maaf, saya tidak punya jawaban untuk itu. Copilot dasar ini hanya menjawab: "
            "output, yield, scrap, OEE, COGM, Cost/Kg. LLM datang di Tahap 3/5.")