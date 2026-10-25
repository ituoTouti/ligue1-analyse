import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1 Analyse", layout="wide", page_icon="⚽")

st.markdown("""
<style>
.stApp {background-color: #0f0f0f; color: white;}
div[data-testid="stMetric"] {background: #1e1e1e; border-radius: 12px; padding: 8px;}
.stButton>button, .stLinkButton>a {background-color: #00c853; color: black; border-radius: 10px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=1800)
def get_league():
    return fetch(BASE + "/leagues?id=53")

@st.cache_data(ttl=900)
def get_team(tid):
    return fetch(BASE + "/teams?id=" + str(tid))

def logo(team_id):
    return "https://images.fotmob.com/image_resources/logo/teamlogo/" + str(team_id) + ".png"

def form_string(form_list, n=5):
    if not form_list:
        return "-"
    return "".join(m.get("resultString", "?") for m in form_list[-n:])

def form_points(form_list, n=5):
    pts = 0
    for m in form_list[-n:]:
        r = m.get("resultString")
        pts += 3 if r == "W" else 1 if r == "D" else 0
    return pts

league = get_league()
if not league:
    st.error("Impossible de charger les données")
    st.stop()

table_data = league["table"][0]["data"]["table"]
team_form_dict = league["table"][0].get("teamForm", {})

def build_df(key):
    rows = []
    for t in table_data.get(key, []):
        rows.append({
            "Pos": t.get("idx"),
            "Equipe": t.get("name"),
            "Pts": t.get("pts"),
            "id": str(t.get("id"))
        })
    return pd.DataFrame(rows).sort_values("Pos") if rows else pd.DataFrame()

df_all = build_df("all")
teams = df_all["Equipe"].tolist()
id_map = dict(zip(df_all["Equipe"], df_all["id"]))

menu = st.sidebar.radio("Menu", ["Analyse", "Classements"])

if menu == "Analyse":
    st.title("Analyse de match")

    home_team = st.selectbox("Domicile", teams)
    away_team = st.selectbox("Exterieur", teams, index=1)

    if home_team == away_team:
        st.warning("Choisis deux equipes differentes")
        st.stop()

    home_id = id_map[home_team]
    away_id = id_map[away_
