import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Ligue 1 Analyse", layout="wide", page_icon="⚽")

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
    return fetch(f"{BASE}/leagues?id=53")

@st.cache_data(ttl=900)
def get_team(tid):
    return fetch(f"{BASE}/teams?id={tid}")

def logo(team_id):
    return f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}.png"

def form_string(form_list, n=5):
    if not form_list:
        return "—"
    return "".join(m.get("resultString", "?") for m in form_list[-n:])

def form_points(form_list, n=5):
    pts = 0
    for m in form_list[-n:]:
        r = m.get("resultString")
        pts += 3 if r == "W" else 1 if r == "D" else 0
    return pts

league = get_league()
if not league:
    st.error("Impossible de charger les données Ligue 1")
    st.stop()

table_data = league["table"][0]["data"]["table"]
team_form_dict = league["table"][0].get("teamForm", {})

def build_df(key):
    rows = []
    for t in table_data.get(key, []):
        rows.append({
            "Pos": t.get("idx"),
            "Équipe": t.get("name"),
            "Pts": t.get("pts"),
            "id": str(t.get("id"))
        })
    return pd.DataFrame(rows).sort_values("Pos") if rows else pd.DataFrame()

df_all = build_df("all")
teams = df_all["Équipe"].tolist()
id_map = dict(zip(df_all["Équipe"], df_all["id"]))

# === SIDEBAR ===
st.sidebar.title("⚽ Ligue 1")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation", ["Analyse de match", "Classements", "À propos"])

if menu == "Analyse de match":
    st.title("Analyse de match")
    st.caption("Forme, xG, absents, contexte et liens bookmakers")

    col1, col2, col3 = st.columns([2, 0.3, 2])
    with col1:
        home_team = st.selectbox("Domicile", teams, index=0)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**vs**")
    with col3:
        away_team = st.selectbox("Extérieur", teams, index=1)

    if home_team == away_team:
        st.warning("Choisis deux équipes différentes")
        st.stop()

    home_id = id_map[home_team]
    away_id = id_map[away_team]

    # Logos
    c1, c2, c3 = st.columns([1, 0.3, 1])
    with c1:
        st.image(logo(home_id), width=80)
        st.subheader(home_team)
    with c2:
        st.markdown("<br><br>**VS**", unsafe_allow_html=True)
    with c3:
        st.image(logo(away_id), width=80)
        st.subheader(away_team)

    home_data = get_team(home_id)
    away_data = get_team(away_id)

    # Forme
    st.subheader("Forme récente")
    c1, c2 = st.columns(2)
    with c1:
        form_h = [m for m in team_form_dict.get(home_id, []) if m.get("home", {}).get("isOurTeam")]
        st.metric("Forme domicile", form_string(form_h))
        st.caption(f"{form_points(form_h)} pts sur 5 matchs")
    with c2:
        form_a = [m for m in team_form_dict.get(away_id, []) if not m.get("home", {}).get("isOurTeam")]
        st.metric("Forme extérieur", form_string(form_a))
        st.caption(f"{form_points(form_a)} pts sur 5 matchs")

    # Absents
    with st.expander("Absents / Blessés"):
        def get_injured(tdata):
            injured = []
            if not tdata:
                return injured
            for group in tdata.get("squad", {}).get("squad", []):
                for p in group.get("members", []):
                    if p.get("injured") or p.get("injury"):
                        inj = p.get("injury", {})
                        ret = inj.get("expectedReturn", "?") if isinstance(inj, dict) else str(inj)
                        injured.append(f"{p.get('name')} ({p.get('role', {}).get('fallback', '')}) — {ret}")
            return injured

        inj_h = get_injured(home_data)
        inj_a = get_injured(away_data)
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**{home_team}**")
            st.write("\n".join(inj_h) if inj_h else "Aucun blessé majeur")
        with c2:
            st.write(f"**{away_team}**")
            st.write("\n".join(inj_a) if inj_a else "Aucun blessé majeur")

    # Côtes
    st.subheader("Côtes bookmakers")
    query = f"{home_team} {away_team}".replace(" ", "%20")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("Betclic", f"https://www.betclic.fr/search?q={query}")
    with c2:
        st.link_button("Winamax", f"https://www.winamax.fr/search?q={query}")
    with c3:
        st.link_button("Unibet", f"https://www.unibet.fr/search?q={query}")

elif menu == "Classements":
    st.title("Classements")
    tab1, tab2, tab3 = st.tabs(["Général", "Domicile", "Extérieur"])
    with tab1:
        st.dataframe(df_all[["Pos", "Équipe", "Pts"]], hide_index=True, use_container_width=True)
    with tab2:
        df_home = build_df("home")
        st.dataframe(df_home[["Pos", "Équipe", "Pts"]], hide_index=True, use_container_width=True)
    with tab3:
        df_away = build_df("away")
        st.dataframe(df_away[["Pos", "Équipe", "Pts"]], hide_index=True, use_container_width=True)

else:
    st.title("À propos")
    st.info("Application d'analyse Ligue 1. Données FotMob. Outil informatif uniquement.")
