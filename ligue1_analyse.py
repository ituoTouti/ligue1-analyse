import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1 Analyse", layout="wide", page_icon="⚽")

st.markdown("""
<style>
.stApp {background-color: #111111; color: #ffffff;}
.stMetric {background-color: #1e1e1e; border-radius: 10px; padding: 8px;}
.stButton>button, .stLinkButton>a {background-color: #00c853; color: black; border-radius: 8px; font-weight: bold;}
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
    st.error("Impossible de charger les donnees")
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
    away_id = id_map[away_team]

    c1, c2, c3 = st.columns([1, 0.3, 1])
    with c1:
        st.image(logo(home_id), width=90)
        st.write("**" + home_team + "**")
    with c2:
        st.write("")
        st.write("**VS**")
    with c3:
        st.image(logo(away_id), width=90)
        st.write("**" + away_team + "**")

    home_data = get_team(home_id)
    away_data = get_team(away_id)

    st.subheader("Forme")
    c1, c2 = st.columns(2)
    with c1:
        form_h = [m for m in team_form_dict.get(home_id, []) if m.get("home", {}).get("isOurTeam")]
        st.metric("Domicile", form_string(form_h), str(form_points(form_h)) + " pts")
    with c2:
        form_a = [m for m in team_form_dict.get(away_id, []) if not m.get("home", {}).get("isOurTeam")]
        st.metric("Exterieur", form_string(form_a), str(form_points(form_a)) + " pts")

    with st.expander("Blesses / Absents"):
        def get_injured(tdata):
            injured = []
            if not tdata:
                return injured
            for group in tdata.get("squad", {}).get("squad", []):
                for p in group.get("members", []):
                    if p.get("injured") or p.get("injury"):
                        injured.append(p.get("name", "Inconnu"))
            return injured
        inj_h = get_injured(home_data)
        inj_a = get_injured(away_data)
        st.write(home_team + " : " + (", ".join(inj_h) if inj_h else "Aucun"))
        st.write(away_team + " : " + (", ".join(inj_a) if inj_a else "Aucun"))

    st.subheader("Cotes")
    query = (home_team + " " + away_team).replace(" ", "%20")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("Betclic", "https://www.betclic.fr/search?q=" + query)
    with c2:
        st.link_button("Winamax", "https://www.winamax.fr/search?q=" + query)
    with c3:
        st.link_button("Unibet", "https://www.unibet.fr/search?q=" + query)

else:
    st.title("Classements")
    tab1, tab2, tab3 = st.tabs(["General", "Domicile", "Exterieur"])
    with tab1:
        st.dataframe(df_all[["Pos", "Equipe", "Pts"]], hide_index=True, use_container_width=True)
    with tab2:
        st.dataframe(build_df("home")[["Pos", "Equipe", "Pts"]], hide_index=True, use_container_width=True)
    with tab3:
        st.dataframe(build_df("away")[["Pos", "Equipe", "Pts"]], hide_index=True, use_container_width=True)
