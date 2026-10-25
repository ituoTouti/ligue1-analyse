import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Ligue 1", layout="centered", page_icon="⚽")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0d4d2e 0%, #1a7a45 100%);
    color: white;
}
h1, h2, h3, label, .stMarkdown {color: white !important;}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 8px;
}
.stButton>button, .stLinkButton>a {
    background: white !important;
    color: #0d4d2e !important;
    border-radius: 10px;
    font-weight: bold;
}
.stExpander {
    background: rgba(255,255,255,0.12);
    border-radius: 12px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE = "https://www.fotmob.com/api/data"

@st.cache_data(ttl=300)
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except:
        return None

@st.cache_data(ttl=300)
def get_league():
    return fetch(BASE + "/leagues?id=53")

@st.cache_data(ttl=300)
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
    st.error("Erreur de chargement")
    st.stop()

table_data = league["table"][0]["data"]["table"]
team_form_dict = league["table"][0].get("teamForm", {})
fixtures = league.get("fixtures", {}).get("allMatches", [])

# Filtrer matchs des 7 derniers jours + prochains
now = datetime.utcnow()
cutoff_past = now - timedelta(days=7)
cutoff_future = now + timedelta(days=7)

matches_list = []
for m in fixtures:
    status = m.get("status", {})
    utc_str = status.get("utcTime", "")
    if not utc_str:
        continue
    try:
        match_time = datetime.fromisoformat(utc_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except:
        continue
    if not (cutoff_past <= match_time <= cutoff_future):
        continue
    home = m.get("home", {})
    away = m.get("away", {})
    if not home.get("name"):
        continue
    score = status.get("scoreStr", "")
    finished = status.get("finished", False)
    time_display = match_time.strftime("%d/%m %H:%M")
    matches_list.append({
        "home": home.get("name"),
        "away": away.get("name"),
        "home_id": str(home.get("id")),
        "away_id": str(away.get("id")),
        "time": time_display,
        "score": score if finished else "",
        "finished": finished,
        "sort": match_time
    })

matches_list.sort(key=lambda x: x["sort"])

st.title("Ligue 1")
st.subheader("Matchs de la semaine")

if not matches_list:
    st.info("Aucun match dans la periode")
else:
    for match in matches_list:
        if match["finished"] and match["score"]:
            label = match["home"] + "  " + match["score"] + "  " + match["away"]
        else:
            label = match["home"] + "  vs  " + match["away"]
        label += "   •   " + match["time"]

        with st.expander(label):
            c1, c2 = st.columns(2)
            with c1:
                st.image(logo(match["home_id"]), width=80)
                st.write("**" + match["home"] + "**")
            with c2:
                st.image(logo(match["away_id"]), width=80)
                st.write("**" + match["away"] + "**")

            form_h = [x for x in team_form_dict.get(match["home_id"], []) if x.get("home", {}).get("isOurTeam")]
            form_a = [x for x in team_form_dict.get(match["away_id"], []) if not x.get("home", {}).get("isOurTeam")]

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Forme domicile", form_string(form_h), str(form_points(form_h)) + " pts")
            with c2:
                st.metric("Forme exterieur", form_string(form_a), str(form_points(form_a)) + " pts")

            home_data = get_team(match["home_id"])
            away_data = get_team(match["away_id"])

            def get_injured(tdata):
                injured = []
                if not tdata:
                    return injured
                for group in tdata.get("squad", {}).get("squad", []):
                    for p in group.get("members", []):
                        if p.get("injured") or p.get("injury"):
                            injured.append(p.get("name", "?"))
                return injured

            inj_h = get_injured(home_data)
            inj_a = get_injured(away_data)

            st.write("**Absents**")
            st.write(match["home"] + " : " + (", ".join(inj_h) if inj_h else "Aucun"))
            st.write(match["away"] + " : " + (", ".join(inj_a) if inj_a else "Aucun"))

            query = (match["home"] + " " + match["away"]).replace(" ", "%20")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.link_button("Betclic", "https://www.betclic.fr/search?q=" + query)
            with c2:
                st.link_button("Winamax", "https://www.winamax.fr/search?q=" + query)
            with c3:
                st.link_button("Unibet", "https://www.unibet.fr/search?q=" + query)

with st.sidebar:
    st.title("Menu")
    if st.button("Classement"):
        rows = []
        for t in table_data.get("all", []):
            rows.append({"Pos": t.get("idx"), "Equipe": t.get("name"), "Pts": t.get("pts")})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
