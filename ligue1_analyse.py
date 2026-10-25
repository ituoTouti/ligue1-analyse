import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1 Analyse", layout="wide", page_icon="⚽", initial_sidebar_state="expanded")

# === THÈME MON PETIT GAZON ===
st.markdown("""
<style>
    .stApp {
        background-color: #0f0f0f;
        color: #ffffff;
    }
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
    }
    h1, h2, h3, h4 {
        color: #ffffff !important;
    }
    .stSelectbox label, .stRadio label {
        color: #cccccc !important;
    }
    div[data-testid="stMetric"] {
        background-color: #1e1e1e;
        border-radius: 12
