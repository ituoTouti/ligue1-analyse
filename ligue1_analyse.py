import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Ligue 1 Analyse & Prédiction", layout="wide", page_icon="⚽")

st.title("⚽ Ligue 1 - Analyse Complète & Aide à la Décision")
st.markdown("**Forme domicile/extérieur, xG, blessés, contexte, H2H, facteurs externes et liens côtes**")
st.caption("Données FotMob (non officiel). Outil d'analyse uniquement. Pariez responsablement.")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BASE = "https://www.fotmob.com/api/data"

@st.cache_data(ttl=1800)
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur données : {e}")
        return None

@st.cache_data(ttl=1800)
def get_league():
    return fetch(f"{BASE}/leagues?id=53")

@st.cache_data(ttl=900)
def get_team(tid):
    return fetch(f"{BASE}/teams?id={tid}")

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
    st.stop()

table_data = league["table"][0]["data"]["table"]
team_form_dict = league["table"][0].get("teamForm", {})

# Build dataframes
def build_df(key):
    rows = []
    for t in table_data.get(key, []):
        rows.append({
            "Pos": t.get("idx"),
            "Équipe": t.get("name"),
            "J": t.get("played"),
            "G": t.get("wins"),
            "N": t.get("draws"),
            "P": t.get("losses"),
            "BP-BC": t.get("scoresStr", "—"),
            "Diff": t.get("goalConDiff"),
            "Pts": t.get("pts"),
            "id": str(t.get("id"))
        })
    return pd.DataFrame(rows).sort_values("Pos") if rows else pd.DataFrame()

df_all = build_df("all")
df_home = build_df("home")
df_away = build_df("away")
df_xg = build_df("xg")  # may have extra xG fields

# Enrich xG if present
if "xg" in table_data and table_data["xg"]:
    xg_rows = []
    for t in table_data["xg"]:
        xg_rows.append({
            "Équipe": t.get("name") or t.get("teamName"),
            "xG": round(t.get("xg", 0), 2),
            "xGA": round(t.get("xgConceded", 0), 2),
            "xPts": round(t.get("xPoints", 0), 2),
            "Diff xG": round(t.get("xgDiff", 0), 2),
            "id": str(t.get("id") or t.get("teamId"))
        })
    df_xg = pd.DataFrame(xg_rows)

teams = df_all["Équipe"].tolist()
id_map = dict(zip(df_all["Équipe"], df_all["id"]))

# === INTERFACE PRINCIPALE ===
st.header("Sélectionner un match")
col1, col2, col3 = st.columns([2, 1, 2])
with col1:
    home_team = st.selectbox("Équipe à domicile", teams, index=0)
with col2:
    st.write("**vs**")
with col3:
    away_team = st.selectbox("Équipe à l'extérieur", teams, index=1)

if home_team == away_team:
    st.warning("Choisis deux équipes différentes.")
    st.stop()

home_id = id_map[home_team]
away_id = id_map[away_team]

home_data = get_team(home_id)
away_data = get_team(away_id)

# === 1. FORME & STATS RÉCENTES ===
st.header("1. Forme et Statistiques Récentes")

c1, c2 = st.columns(2)
with c1:
    st.subheader(f"{home_team} (Domicile)")
    form_h = team_form_dict.get(home_id, [])
    # Filter roughly home (isOurTeam True on home side)
    home_forms = [m for m in form_h if m.get("home", {}).get("isOurTeam")][-5:]
    st.metric("Forme domicile (5)", form_string(home_forms))
    st.metric("Pts forme domicile", form_points(home_forms))
    home_row = df_home[df_home["Équipe"] == home_team]
    if not home_row.empty:
        st.write(f"Classement domicile : **{home_row.iloc[0]['Pos']}** | {home_row.iloc[0]['Pts']} pts")

with c2:
    st.subheader(f"{away_team} (Extérieur)")
    form_a = team_form_dict.get(away_id, [])
    away_forms = [m for m in form_a if not m.get("home", {}).get("isOurTeam")][-5:]
    st.metric("Forme extérieur (5)", form_string(away_forms))
    st.metric("Pts forme extérieur", form_points(away_forms))
    away_row = df_away[df_away["Équipe"] == away_team]
    if not away_row.empty:
        st.write(f"Classement extérieur : **{away_row.iloc[0]['Pos']}** | {away_row.iloc[0]['Pts']} pts")

st.subheader("xG (saison) — Surperformance / Sous-performance")
if not df_xg.empty:
    xg_h = df_xg[df_xg["Équipe"] == home_team]
    xg_a = df_xg[df_xg["Équipe"] == away_team]
    if not xg_h.empty and not xg_a.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**{home_team}** : xG {xg_h.iloc[0]['xG']} | xGA {xg_h.iloc[0]['xGA']} | xPts {xg_h.iloc[0]['xPts']}")
            diff = xg_h.iloc[0].get("Diff xG", 0)
            st.caption("Positif = surperforme (chance) | Négatif = sous-performe (malchance)" if "Diff xG" in xg_h.columns else "")
        with c2:
            st.write(f"**{away_team}** : xG {xg_a.iloc[0]['xG']} | xGA {xg_a.iloc[0]['xGA']} | xPts {xg_a.iloc[0]['xPts']}")
else:
    st.info("Données xG détaillées non disponibles pour le moment.")

# === 2. EFFECTIFS & ABSENCES ===
st.header("2. Effectifs et Absences")

def get_injured(tdata):
    injured = []
    if not tdata:
        return injured
    for group in tdata.get("squad", {}).get("squad", []):
        for p in group.get("members", []):
            if p.get("injured") or p.get("injury"):
                inj = p.get("injury", {})
                ret = inj.get("expectedReturn", "Inconnu") if isinstance(inj, dict) else str(inj)
                injured.append({
                    "Joueur": p.get("name"),
                    "Poste": p.get("role", {}).get("fallback", ""),
                    "Retour estimé": ret,
                    "Note": p.get("rating")
                })
    return injured

inj_h = get_injured(home_data)
inj_a = get_injured(away_data)

c1, c2 = st.columns(2)
with c1:
    st.subheader(f"Absents {home_team}")
    if inj_h:
        st.dataframe(pd.DataFrame(inj_h), hide_index=True, use_container_width=True)
    else:
        st.success("Aucun blessé majeur signalé")
with c2:
    st.subheader(f"Absents {away_team}")
    if inj_a:
        st.dataframe(pd.DataFrame(inj_a), hide_index=True, use_container_width=True)
    else:
        st.success("Aucun blessé majeur signalé")

st.caption("Vérifie toujours les feuilles officielles 1h avant le coup d'envoi (suspensions, retours tardifs).")

# === 3. CONTEXTE & ENJEU ===
st.header("3. Contexte et Enjeu Sportif")
pos_h = int(df_all[df_all["Équipe"] == home_team].iloc[0]["Pos"])
pos_a = int(df_all[df_all["Équipe"] == away_team].iloc[0]["Pos"])

def stake(pos):
    if pos <= 3:
        return "Titre / Places européennes (CL)"
    elif pos <= 6:
        return "Europe (EL / Conference)"
    elif pos >= 16:
        return "Maintien / Barrage"
    else:
        return "Ventre mou (motivation variable)"

c1, c2 = st.columns(2)
with c1:
    st.write(f"**{home_team}** : {pos_h}ème → {stake(pos_h)}")
with c2:
    st.write(f"**{away_team}** : {pos_a}ème → {stake(pos_a)}")

st.info("Fatigue Europe : vérifie le calendrier midweek (Champions / Europa / Conference). Un déplacement en Europe impacte souvent le week-end suivant.")

# === 4. HISTORIQUE H2H ===
st.header("4. Historique et Psychologie")
st.markdown("**Confrontations directes** (derniers résultats disponibles via forme récente)")
# Simple extraction from recent form
h2h_matches = []
for m in (team_form_dict.get(home_id, []) + team_form_dict.get(away_id, [])):
    tt = m.get("tooltipText", {})
    if {tt.get("homeTeam"), tt.get("awayTeam")} == {home_team, away_team} or \
       (tt.get("homeTeam") in [home_team, away_team] and tt.get("awayTeam") in [home_team, away_team]):
        h2h_matches.append(f"{tt.get('homeTeam')} {tt.get('homeScore')}-{tt.get('awayScore')} {tt.get('awayTeam')}")

if h2h_matches:
    for m in list(dict.fromkeys(h2h_matches))[-4:]:
        st.write(f"- {m}")
else:
    st.info("Pas de H2H récent dans les 5 derniers matchs. Consulte les archives pour les derbies (Olympico, Derby du Nord, etc.).")

st.caption("Derby / Rivalité : l'intensité émotionnelle peut renverser la hiérarchie du classement.")

# === 5. FACTEURS EXTERNES ===
st.header("5. Facteurs Externes et Environnementaux")
st.markdown("""
- **Avantage domicile** : historiquement ~46-50 % de victoires à domicile en Ligue 1.
- **Météo** : terrain lourd/pluie → avantage au jeu direct et aux équipes physiques.
- **Arbitrage** : profil de l'arbitre (cartons, penalties) à vérifier sur les sites spécialisés.
""")

# === 6. ANALYSE TACTIQUE ===
st.header("6. Analyse Tactique (Matchup)")
st.markdown("""
Compare les styles :
- Possession haute vs contre-attaque
- Efficacité sur phases arrêtées (corners / coups francs = fort % des buts en L1)
- Profondeur de banc et capacité de rotation
""")

# === CÔTES ===
st.header("Côtes des 3 plus grands bookmakers")
st.markdown("Clique pour ouvrir directement la recherche du match :")

query = f"{home_team} {away_team} Ligue 1".replace(" ", "%20")
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("Betclic", f"https://www.betclic.fr/search?q={query}")
with c2:
    st.link_button("Winamax", f"https://www.winamax.fr/search?q={query}")
with c3:
    st.link_button("Unibet", f"https://www.unibet.fr/search?q={query}")

st.caption("Les côtes évoluent en temps réel. Vérifie toujours sur le site officiel avant de parier.")

# === SUGGESTION SIMPLE ===
st.header("Suggestion d'analyse")
form_h_pts = form_points([m for m in team_form_dict.get(home_id, []) if m.get("home", {}).get("isOurTeam")])
form_a_pts = form_points([m for m in team_form_dict.get(away_id, []) if not m.get("home", {}).get("isOurTeam")])
inj_diff = len(inj_a) - len(inj_h)
score = (form_h_pts - form_a_pts) + 2 + (inj_diff * 0.5)  # home +2 bonus

if score > 3:
    suggestion = f"Léger avantage **{home_team}** (forme domicile + avantage terrain)"
elif score < -1:
    suggestion = f"Léger avantage **{away_team}** (meilleure forme extérieur / moins d'absents)"
else:
    suggestion = "Match équilibré — regarde les absents clés et le contexte."

st.success(suggestion)
st.caption("Modèle simple basé sur forme domicile/extérieur + absences. Pas une prédiction garantie.")

st.sidebar.header("Classements rapides")
with st.sidebar.expander("Classement général"):
    st.dataframe(df_all[["Pos", "Équipe", "Pts"]], hide_index=True)
with st.sidebar.expander("Classement domicile"):
    st.dataframe(df_home[["Pos", "Équipe", "Pts"]], hide_index=True)
with st.sidebar.expander("Classement extérieur"):
    st.dataframe(df_away[["Pos", "Équipe", "Pts"]], hide_index=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Rafraîchir** pour données à jour (cache 30 min).")
