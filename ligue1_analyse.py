import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="Ligue 1 Analyse", layout="centered", page_icon="⚽")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(160deg, #0a3d26 0%, #146c3a 100%);
    color: #ffffff;
}
h1, h2, h3 {
    text-decoration: underline;
    text-underline-offset: 4px;
}
.stExpander {
    border-radius: 14px;
    margin-bottom: 12px;
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

def form_vnd(form_list, n=5):
    if not form_list:
        return "-"
    mapping = {"W": "V", "D": "N", "L": "D"}
    return " ".join(mapping.get(m.get("resultString", "?"), "?") for m in form_list[-n:])

def form_points(form_list, n=5):
    pts = 0
    for m in form_list[-n:]:
        r = m.get("resultString")
        pts += 3 if r == "W" else 1 if r == "D" else 0
    return pts

def analyse_equipe(pos, form_pts, is_home):
    fort = []
    faible = []
    if pos <= 6:
        fort.append("classement solide")
    else:
        faible.append("classement fragile")
    if form_pts >= 10:
        fort.append("excellente dynamique")
    elif form_pts <= 4:
        faible.append("dynamique negative")
    if is_home:
        fort.append("avantage domicile")
    else:
        faible.append("deplacement")
    return (", ".join(fort) if fort else "aucun"), (", ".join(faible) if faible else "aucun")

def pronostic_score(home_pos, away_pos, pts_h, pts_a):
    if pts_h >= 10 and home_pos < away_pos:
        return "2-0"
    elif pts_h >= 7 and home_pos <= away_pos:
        return "2-1"
    elif pts_a >= 10 and away_pos < home_pos:
        return "0-2"
    elif pts_a >= 7 and away_pos <= home_pos:
        return "1-2"
    elif abs(home_pos - away_pos) <= 2:
        return "1-1"
    else:
        return "1-0" if home_pos < away_pos else "0-1"

league = get_league()
if not league:
    st.error("Erreur de chargement")
    st.stop()

table_data = league["table"][0]["data"]["table"]
team_form_dict = league["table"][0].get("teamForm", {})
fixtures = league.get("fixtures", {}).get("allMatches", [])

pos_map = {}
for t in table_data.get("all", []):
    pos_map[t.get("name")] = t.get("idx")

by_round = defaultdict(list)
now = datetime.utcnow()

for m in fixtures:
    status = m.get("status", {})
    utc_str = status.get("utcTime", "")
    if not utc_str:
        continue
    try:
        match_time = datetime.fromisoformat(utc_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except:
        continue
    home = m.get("home", {})
    away = m.get("away", {})
    if not home.get("name"):
        continue
    round_num = str(m.get("round", "?"))
    if not round_num.isdigit():
        continue
    rnd = int(round_num)
    if rnd > 15:
        continue
    score = status.get("scoreStr", "")
    finished = status.get("finished", False)
    by_round[rnd].append({
        "home": home.get("name"),
        "away": away.get("name"),
        "home_id": str(home.get("id")),
        "away_id": str(away.get("id")),
        "time": match_time.strftime("%d/%m %H:%M"),
        "score": score if finished else "",
        "finished": finished,
        "sort": match_time,
        "is_past": match_time < now - timedelta(hours=3),
        "is_current": abs((match_time - now).days) <= 2
    })

st.title("Ligue 1 Analyse")
st.subheader("Matchs par journee")

sorted_rounds = sorted(by_round.keys())

for rnd in sorted_rounds:
    matches = sorted(by_round[rnd], key=lambda x: x["sort"])
    all_finished = all(m["finished"] for m in matches)
    any_current = any(m["is_current"] and not m["finished"] for m in matches)

    # Couleur selon statut
    if all_finished:
        color = "#6b7280"  # gris
    elif any_current:
        color = "#16a34a"  # vert
    else:
        color = "#1e3a8a"  # bleu fonce

    st.markdown(f"""
    <div style="background-color:{color}; padding:10px; border-radius:12px; margin-bottom:8px;">
        <strong>Journee {rnd}</strong>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Voir les matchs"):
        for match in matches:
            if match["finished"] and match["score"]:
                label = match["home"] + " " + match["score"].replace(" - ", " – ") + " " + match["away"]
            else:
                label = match["home"] + " vs " + match["away"]
            label += "  •  " + match["time"]

            with st.expander(label):
                form_h = [x for x in team_form_dict.get(match["home_id"], []) if x.get("home", {}).get("isOurTeam")]
                form_a = [x for x in team_form_dict.get(match["away_id"], []) if not x.get("home", {}).get("isOurTeam")]

                c1, c2 = st.columns(2)
                with c1:
                    st.image(logo(match["home_id"]), width=70)
                    st.write("**" + match["home"] + "**")
                    st.caption(form_vnd(form_h))
                with c2:
                    st.image(logo(match["away_id"]), width=70)
                    st.write("**" + match["away"] + "**")
                    st.caption(form_vnd(form_a))

                if not match["finished"]:
                    home_pos = pos_map.get(match["home"], 10)
                    away_pos = pos_map.get(match["away"], 10)
                    pts_h = form_points(form_h)
                    pts_a = form_points(form_a)

                    score_pred = pronostic_score(home_pos, away_pos, pts_h, pts_a)
                    st.markdown("**Pronostic score exact**")
                    st.write(score_pred)

                    fort_h, faible_h = analyse_equipe(home_pos, pts_h, True)
                    fort_a, faible_a = analyse_equipe(away_pos, pts_a, False)

                    st.markdown("**Analyse**")
                    st.write(match["home"] + " — Fort : " + fort_h)
                    st.write(match["home"] + " — Faible : " + faible_h)
                    st.write(match["away"] + " — Fort : " + fort_a)
                    st.write(match["away"] + " — Faible : " + faible_a)

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
                st.markdown("**Absents**")
                st.write(match["home"] + " : " + (", ".join(inj_h) if inj_h else "Aucun"))
                st.write(match["away"] + " : " + (", ".join(inj_a) if inj_a else "Aucun"))

with st.sidebar:
    st.title("Menu")
    if st.button("Classement"):
        rows = []
        for t in table_data.get("all", []):
            rows.append({"Pos": t.get("idx"), "Equipe": t.get("name"), "Pts": t.get("pts")})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
