import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1 Analyse", layout="wide", page_icon="⚽")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0d4d2e 0%, #1a7a45 50%, #0d4d2e 100%);
    color: #ffffff;
}
h1, h2, h3, h4, .stMarkdown, label {
    color: #ffffff !important;
}
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}
.stButton>button, .stLinkButton>a {
    background-color: #ffffff !important;
    color: #0d4d2e !important;
    border-radius: 10px !important;
    font-weight: bold !important;
}
.stSelectbox div[data-baseweb="select"] {
    background-color: rgba(255, 255, 255, 0.15);
}
.stExpander {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
}
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
            "J": t.get("played"),
            "V": t.get("wins"),
            "N": t.get("draws"),
            "D": t.get("losses"),
            "id": str(t.get("id"))
        })
    return pd.DataFrame(rows).sort_values("Pos") if rows else pd.DataFrame()

df_all = build_df("all")
teams = df_all["Equipe"].tolist()
id_map = dict(zip(df_all["Equipe"], df_all["id"]))
pos_map = dict(zip(df_all["Equipe"], df_all["Pos"]))

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
        st.image(logo(home_id), width=100)
        st.markdown("**" + home_team + "**")
        st.caption("Position : " + str(pos_map.get(home_team, "?")))
    with c2:
        st.markdown("<br><br><center><h2>VS</h2></center>", unsafe_allow_html=True)
    with c3:
        st.image(logo(away_id), width=100)
        st.markdown("**" + away_team + "**")
        st.caption("Position : " + str(pos_map.get(away_team, "?")))

    home_data = get_team(home_id)
    away_data = get_team(away_id)

    st.subheader("Forme recente")
    c1, c2 = st.columns(2)
    with c1:
        form_h = [m for m in team_form_dict.get(home_id, []) if m.get("home", {}).get("isOurTeam")]
        st.metric("Domicile", form_string(form_h, 5), str(form_points(form_h, 5)) + " pts")
    with c2:
        form_a = [m for m in team_form_dict.get(away_id, []) if not m.get("home", {}).get("isOurTeam")]
        st.metric("Exterieur", form_string(form_a, 5), str(form_points(form_a, 5)) + " pts")

    st.subheader("Contexte")
    home_pos = pos_map.get(home_team, 20)
    away_pos = pos_map.get(away_team, 20)
    if home_pos <= 4 and away_pos <= 4:
        st.success("Match pour le haut de tableau")
    elif home_pos >= 15 or away_pos >= 15:
        st.warning("Enjeu de relégation possible")
    else:
        st.info("Match de milieu de tableau")

    with st.expander("Absents / Blesses"):
        def get_injured(tdata):
            injured = []
            if not tdata:
                return injured
            for group in tdata.get("squad", {}).get("squad", []):
                for p in group.get("members", []):
                    if p.get("injured") or p.get("injury"):
                        role = p.get("role", {}).get("fallback", "")
                        injured.append(p.get("name", "?") + " (" + role + ")")
            return injured
        inj_h = get_injured(home_data)
        inj_a = get_injured(away_data)
        c1, c2 = st.columns(2)
        with c1:
            st.write("**" + home_team + "**")
            st.write(", ".join(inj_h) if inj_h else "Aucun")
        with c2:
            st.write("**" + away_team + "**")
            st.write(", ".join(inj_a) if inj_a else "Aucun")

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
        st.dataframe(df_all[["Pos", "Equipe", "Pts", "J", "V", "N", "D"]], hide_index=True, use_container_width=True)
    with tab2:
        st.dataframe(build_df("home")[["Pos", "Equipe", "Pts", "J", "V", "N", "D"]], hide_index=True, use_container_width=True)
    with tab3:
        st.dataframe(build_df("away")[["Pos", "Equipe", "Pts", "J", "V", "N", "D"]], hide_index=True, use_container_width=True)
