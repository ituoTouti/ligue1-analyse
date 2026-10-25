import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE = "https://www.fotmob.com/api/data"

@st.cache_data(ttl=1800)
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except:
        return None

league = fetch(BASE + "/leagues?id=53")
if not league:
    st.error("Erreur chargement")
    st.stop()

table = league["table"][0]["data"]["table"]["all"]
teams = [t["name"] for t in table]
ids = {t["name"]: str(t["id"]) for t in table}

st.title("Analyse Ligue 1")

home = st.selectbox("Domicile", teams)
away = st.selectbox("Exterieur", teams, index=1)

if home == away:
    st.warning("Deux equipes differentes")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    st.subheader(home)
    st.image("https://images.fotmob.com/image_resources/logo/teamlogo/" + ids[home] + ".png", width=80)
with col2:
    st.subheader(away)
    st.image("https://images.fotmob.com/image_resources/logo/teamlogo/" + ids[away] + ".png", width=80)

st.subheader("Cotes")
q = (home + " " + away).replace(" ", "%20")
st.link_button("Betclic", "https://www.betclic.fr/search?q=" + q)
st.link_button("Winamax", "https://www.winamax.fr/search?q=" + q)
st.link_button("Unibet", "https://www.unibet.fr/search?q=" + q)
