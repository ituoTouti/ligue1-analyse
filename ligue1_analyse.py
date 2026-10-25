import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(
    page_title="Ligue 1 Pro",
    layout="centered",
    page_icon="⚽",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(165deg, #071f14 0%, #0f3d28 50%, #0a2e1c 100%);
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
h1 {
    font-weight: 700;
    border-bottom: 3px solid #22c55e;
    padding-bottom: 10px;
}
h2 {
    color: #bbf7d0;
    font-weight: 600;
}
.stExpander {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 16px;
    margin-bottom: 16px;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    margin-right: 8px;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: #16a34a !important;
    color: white !important;
    font-weight: 600;
}
.stButton>button {
    background: #16a34a;
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
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
        return "—"
    mapping = {"W": "V", "D": "N", "L": "D"}
    last = form_list[-n:] if len(form_list) >= n else form_list
    return " ".join(mapping.get(m.get("resultString", "?"), "?") for m in last)

def form_points(form_list, n=5):
    pts = 0
    last = form_list[-n:] if form_list else []
    for m in last:
        r = m.get("resultString")
        pts += 3 if r == "W" else 1 if r == "D" else 0
    return pts

def pronostic_complet(home, away, home_pos, away_pos, pts_h, pts_a):
    if pts_h >= 10 and home_pos < away_pos:
        score = "2-0"
        buteurs = f"Buts de {home}"
    elif pts_h >= 7 and home_pos <= away_pos:
        score = "2-1"
        buteurs = f"Buts de {home} et un but de {away}"
    elif pts_a >= 10 and away_pos < home_pos:
        score = "0-2"
        buteurs = f"Buts de {away}"
    elif pts_a >= 7 and away_pos <= home_pos:
        score = "1-2"
        buteurs = f"But de {home} et buts de {away}"
    elif abs(home_pos - away_pos) <= 2:
        score = "1-1"
        buteurs = f"Un but de chaque côté"
    else:
        score = "1-0" if home_pos < away_pos else "0-1"
        buteurs = f"But de {home if home_pos < away_pos else away}"
    return score, buteurs

def analyse_longue(home, away, home_pos, away_pos, pts_h, pts_a, form_h, form_a, inj_h, inj_a, finished, score):
    if finished:
        return (
            f"**Résultat final** : {home} {score.replace(' - ', ' – ')} {away}.\n\n"
            f"Avant cette rencontre, {home} se situait à la {home_pos}e place du classement avec une forme récente de {form_h} "
            f"({pts_h} points sur les 5 derniers matchs). {away} occupait la {away_pos}e place avec une série de {form_a} "
            f"({pts_a} points).\n\n"
            f"Le match s’est joué dans un contexte où les enjeux de classement restaient importants pour les deux formations. "
            + (f"Les absences principales concernaient {', '.join((inj_h + inj_a)[:3])}." if (inj_h or inj_a) else "Peu d’absences majeures ont été signalées des deux côtés.")
            + "\n\nCe résultat confirme la hiérarchie actuelle de la Ligue 1 sur cette période."
        )
    else:
        texte = (
            f"**Analyse de la rencontre**\n\n"
            f"{home} ({home_pos}e, forme {form_h} — {pts_h} pts) reçoit {away} ({away_pos}e, forme {form_a} — {pts_a} pts) "
            f"dans un match qui s’annonce intéressant au regard des positions au classement.\n\n"
        )
        if home_pos < away_pos and pts_h >= pts_a:
            texte += f"{home} dispose d’un avantage clair grâce à son meilleur classement et à l’avantage du terrain. L’équipe locale devrait contrôler la rencontre et se créer les meilleures occasions.\n\n"
        elif away_pos < home_pos and pts_a > pts_h:
            texte += f"{away} arrive en meilleure dynamique et avec un meilleur classement. Les visiteurs ont les moyens de prendre le dessus même en déplacement.\n\n"
        else:
            texte += f"Les deux équipes présentent des profils proches. Le match devrait être serré et se jouer sur des détails, notamment l’efficacité devant le but et la solidité défensive.\n\n"

        if inj_h:
            texte += f"**Absences {home}** : {', '.join(inj_h[:3])}. Ces manques pourraient influencer le collectif.\n"
        if inj_a:
            texte += f"**Absences {away}** : {', '.join(inj_a[:3])}.\n"

        texte += "\n**Lecture finale** : la première équipe qui ouvrira le score prendra un avantage psychologique important dans cette confrontation."
        return texte

league = get_league()
if not league:
    st.error("Impossible de charger les données.")
    st.stop()

table_data = league["table"][0]["data"]["table"]
team_form_dict = league["table"][0].get("teamForm", {})
fixtures = league.get("fixtures", {}).get("allMatches", [])

pos_map = {t.get("name"): t.get("idx") for t in table_data.get("all", [])}

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
    if rnd > 16:
        continue
    score = status.get("scoreStr", "")
    finished = status.get("finished", False)
    by_round[rnd].append({
        "home": home.get("name"),
        "away": away.get("name"),
        "home_id": str(home.get("id")),
        "away_id": str(away.get("id")),
        "time": match_time.strftime("%d/%m • %H:%M"),
        "score": score if finished else "",
        "finished": finished,
        "sort": match_time,
        "is_current": abs((match_time - now).total_seconds()) < 48 * 3600
    })

st.title("Ligue 1 Pro")
st.caption("Analyses détaillées • Forme • Absences • Pronostics")

sorted_rounds = sorted(by_round.keys())

for rnd in sorted_rounds:
    matches = sorted(by_round[rnd], key=lambda x: x["sort"])
    all_finished = all(m["finished"] for m in matches)
    any_current = any(m["is_current"] and not m["finished"] for m in matches)

    if all_finished:
        color = "#4b5563"
    elif any_current:
        color = "#16a34a"
    else:
        color = "#1e40af"

    st.markdown(f"""
    <div style="background:{color}; padding:14px 18px; border-radius:12px; margin:10px 0; font-weight:600; font-size:1.05rem;">
        Journée {rnd}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Voir les matchs de la journée"):
        for match in matches:
            if match["finished"] and match["score"]:
                label = f"{match['home']}  {match['score'].replace(' - ', ' – ')}  {match['away']}"
            else:
                label = f"{match['home']}  vs  {match['away']}"
            label += f"   •   {match['time']}"

            with st.expander(label):
                form_h = team_form_dict.get(match["home_id"], [])
                form_a = team_form_dict.get(match["away_id"], [])

                c1, c2 = st.columns(2)
                with c1:
                    st.image(logo(match["home_id"]), width=75)
                    st.markdown(f"**{match['home']}**")
                    st.caption(form_vnd(form_h, 5))
                with c2:
                    st.image(logo(match["away_id"]), width=75)
                    st.markdown(f"**{match['away']}**")
                    st.caption(form_vnd(form_a, 5))

                tabs = st.tabs(["Résumé", "Compositions", "Tête-à-tête", "Classement"])

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

                home_pos = pos_map.get(match["home"], 10)
                away_pos = pos_map.get(match["away"], 10)
                pts_h = form_points(form_h)
                pts_a = form_points(form_a)

                with tabs[0]:
                    st.markdown(analyse_longue(
                        match["home"], match["away"], home_pos, away_pos,
                        pts_h, pts_a, form_vnd(form_h, 5), form_vnd(form_a, 5),
                        inj_h, inj_a, match["finished"], match["score"]
                    ))
                    if not match["finished"]:
                        score_pred, buteurs = pronostic_complet(match["home"], match["away"], home_pos, away_pos, pts_h, pts_a)
                        st.markdown("**Pronostic**")
                        st.write(f"Score exact : **{score_pred}**")
                        st.write(f"Buteurs potentiels : {buteurs}")

                with tabs[1]:
                    st.write(f"**{match['home']}** : {', '.join(inj_h) if inj_h else 'Aucun absent majeur'}")
                    st.write(f"**{match['away']}** : {', '.join(inj_a) if inj_a else 'Aucun absent majeur'}")

                with tabs[2]:
                    st.write(f"**{match['home']}** : {form_vnd(form_h, 5)} ({pts_h} pts)")
                    st.write(f"**{match['away']}** : {form_vnd(form_a, 5)} ({pts_a} pts)")

                with tabs[3]:
                    st.markdown("**Classement actuel Ligue 1**")
                    rows = []
                    for t in table_data.get("all", []):
                        rows.append({"Pos": t.get("idx"), "Équipe": t.get("name"), "Pts": t.get("pts")})
                    df = pd.DataFrame(rows)
                    st.dataframe(df, hide_index=True, use_container_width=True)

with st.sidebar:
    st.markdown("### Ligue 1 Pro")
    st.caption("Analyses professionnelles")
