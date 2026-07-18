
from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Observatoire législatif", page_icon="⚖️", layout="wide")
DB = Path(__file__).parent / "database" / "legislation.sqlite"

@st.cache_resource
def connection():
    return sqlite3.connect(DB, check_same_thread=False)

@st.cache_data
def query(sql):
    return pd.read_sql_query(sql, connection())

textes = query("SELECT * FROM textes")
scrutins = query("SELECT * FROM scrutins")
amendements = query("SELECT * FROM amendements")
acteurs = query("SELECT * FROM acteurs")
votes = query("SELECT * FROM votes_individuels")
actes = query("SELECT * FROM actes_reglementaires")
groupes = query("SELECT * FROM groupes")
positions_groupes = query("SELECT * FROM positions_groupes")
statut_imports = query("SELECT * FROM statut_imports")
sources = query("SELECT * FROM sources")

st.title("Observatoire législatif")
st.caption("V4 · Textes, scrutins, amendements, acteurs et mesure du clivage")

with st.sidebar:
    niveaux = st.multiselect("Niveau", sorted(textes.niveau.unique()), default=sorted(textes.niveau.unique()))
    institutions = st.multiselect("Institution", sorted(textes.institution.unique()), default=sorted(textes.institution.unique()))
    themes = st.multiselect("Thème", sorted(textes.theme.unique()), default=sorted(textes.theme.unique()))
    recherche = st.text_input("Recherche")

vue = textes[
    textes.niveau.isin(niveaux)
    & textes.institution.isin(institutions)
    & textes.theme.isin(themes)
].copy()

if recherche:
    x = recherche.lower()
    vue = vue[
        vue.titre.str.lower().str.contains(x, na=False)
        | vue.presentateur.str.lower().str.contains(x, na=False)
        | vue.theme.str.lower().str.contains(x, na=False)
    ]

a,b,c,d = st.columns(4)
a.metric("Textes", len(textes))
b.metric("Scrutins", len(scrutins))
c.metric("Amendements", len(amendements))
d.metric("Votes individuels", len(votes))

st.warning(
    "Cette V4 contient un échantillon vérifié, pas encore l'intégralité des travaux parlementaires. "
    "Les connecteurs de collecte massive sont préparés, mais les votes nominatifs restent à importer."
)

tabs = st.tabs([
    "Tableau de bord","Textes","Fiche texte","Scrutins","Votes et clivage",
    "Amendements","Groupes","Élus","Actes réglementaires","Imports","Méthode","Sources"
])

with tabs[0]:
    st.subheader("Activité recensée")
    c1,c2 = st.columns(2)
    with c1:
        by_theme = textes.groupby("theme", as_index=False).size()
        st.plotly_chart(px.bar(by_theme, x="theme", y="size", text="size",
                               labels={"theme":"","size":"Textes"}), width="stretch")
    with c2:
        resultats = scrutins.groupby("resultat", as_index=False).size()
        st.plotly_chart(px.pie(resultats, names="resultat", values="size"), width="stretch")

    numeric = scrutins.dropna(subset=["indice_clivage"])
    if not numeric.empty:
        st.subheader("Scrutins les plus clivants")
        chart = numeric.sort_values("indice_clivage", ascending=False)
        st.plotly_chart(px.bar(
            chart, x="indice_clivage", y="objet", orientation="h",
            text="indice_clivage",
            labels={"indice_clivage":"Indice de clivage","objet":""}
        ), width="stretch")

with tabs[1]:
    st.dataframe(vue, width="stretch", hide_index=True)

with tabs[2]:
    if len(vue):
        titre = st.selectbox("Texte", vue.titre.sort_values())
        r = vue[vue.titre == titre].iloc[0]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Institution", r.institution)
        c2.metric("Type", r.type_texte)
        c3.metric("Statut", r.statut)
        c4.metric("Thème", r.theme)
        st.markdown(f"## {r.titre}")
        st.write(f"**Présentateur :** {r.presentateur}")
        st.write(f"**Origine :** {r.origine}")
        st.markdown(f"[Dossier officiel]({r.url_officielle})")
        st.subheader("Scrutins liés")
        st.dataframe(scrutins[scrutins.texte_id == r.texte_id], width="stretch", hide_index=True)
        st.subheader("Amendements liés")
        st.dataframe(amendements[amendements.texte_id == r.texte_id], width="stretch", hide_index=True)

with tabs[3]:
    st.dataframe(scrutins, width="stretch", hide_index=True)

with tabs[4]:
    numeric = scrutins.dropna(subset=["pour","contre"]).copy()
    if not numeric.empty:
        selected = st.selectbox("Scrutin", numeric.scrutin_id.tolist())
        row = numeric[numeric.scrutin_id == selected].iloc[0]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Pour", int(row["pour"]))
        c2.metric("Contre", int(row["contre"]))
        c3.metric("Abstentions", int(row["abstention"]))
        c4.metric("Clivage", row["niveau_clivage"])
        chart = pd.DataFrame({
            "Position":["Pour","Contre","Abstention"],
            "Voix":[row["pour"],row["contre"],row["abstention"]]
        })
        st.plotly_chart(px.bar(chart, x="Position", y="Voix", text="Voix"), width="stretch")
        st.caption(
            "Indice de clivage = 100 moins la part du camp majoritaire parmi les suffrages exprimés. "
            "Il mesure l'équilibre du vote, pas son importance politique."
        )
    if votes.empty:
        st.info("Aucun vote individuel n'est encore chargé. La table et les vues sont prêtes.")

with tabs[5]:
    st.dataframe(amendements, width="stretch", hide_index=True)

with tabs[6]:
    st.dataframe(groupes, width="stretch", hide_index=True)
    if positions_groupes.empty:
        st.info("Les positions détaillées par groupe seront alimentées par les imports officiels.")

with tabs[7]:
    st.dataframe(acteurs, width="stretch", hide_index=True)
    if votes.empty:
        st.warning("Les fiches d'élus deviendront pertinentes après import des votes nominatifs.")

with tabs[8]:
    if actes.empty:
        st.info("Les décrets et arrêtés seront intégrés via l'API Légifrance / PISTE.")
    else:
        st.dataframe(actes, width="stretch", hide_index=True)

with tabs[9]:
    st.dataframe(statut_imports, width="stretch", hide_index=True)
    st.markdown("""
    **Ordre recommandé**
    1. votes publics de l'Assemblée nationale ;
    2. scrutins et analyses de groupes du Sénat ;
    3. amendements ;
    4. votes nominatifs du Parlement européen ;
    5. lois promulguées et décrets d'application via Légifrance.
    """)

with tabs[10]:
    st.markdown("""
    - **Soutien brut** : vote pour.
    - **Opposition brute** : vote contre.
    - **Abstention** : position autonome.
    - **Discipline de groupe** : part des votants alignés sur la position majoritaire du groupe.
    - **Dissidence** : vote différent de la majorité du groupe.
    - **Clivage** : équilibre entre pour et contre ; ce n'est pas un jugement de valeur.
    - Un vote non public ne permet pas nécessairement d'identifier chaque votant.
    """)

with tabs[11]:
    st.dataframe(sources, width="stretch", hide_index=True)
