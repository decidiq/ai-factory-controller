"""Gaya tampilan (palet netral industri: #0f172a, #f8fafc, #3b82f6)."""
import streamlit as st

CSS = """
<style>
.stApp { background-color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
[data-testid="stSidebar"] { background-color: #0f172a; color: #ffffff; }
[data-testid="stSidebar"] .stRadio label { color: #f1f5f9 !important; font-weight: 500; }
div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 14px;
    border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
h1, h2, h3 { color: #0f172a; font-weight: 700; }
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
