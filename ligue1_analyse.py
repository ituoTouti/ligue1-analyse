import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1 Analyse", layout="wide", page_icon="⚽", initial_sidebar_state="expanded")

# Thème style Mon Petit Gazon
css = """
<style>
.stApp {background-color: #0f0f0f; color: #ffffff;}
.sidebar .sidebar-content {background-color: #1a1a1a;}
h1, h2, h3, h4 {color: #ffffff !important;}
.stSelectbox label, .stRadio label {color: #cccccc !important;}
div[data-testid="stMetric"] {
    background-color: #1e1e1e;
    border-radius: 12px;
    padding: 10px;
    border: 1px solid #2a2a2a;
}
.stButton>button, .stLinkButton>a {
    background-color: #00c853 !important;
    color: #000000 !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton>button:hover, .stLinkButton>a:hover {
    background-color: #00e676 !important;
}
.stTabs [data-baseweb="tab-list"] {gap: 8px;}
.stTabs [data-baseweb="tab"] {
    background-color: #1e1e1e;
    border-radius: 10px;
    color: #ffffff;
}
.stTabs [aria-selected="true"] {
    background-color: #00c853 !important;
    color: #000000 !important;
}
div[data-testid="stExpander"] {
    background-color: #1a1a1a;
    border-radius: 12px;
    border: 1px solid #2a2a2a;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

HEADERS = {"
