
from pathlib import Path
import sqlite3
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Qui vote quoi", page_icon="🗳️", layout="wide")

BASE = Path(__file__).parent
SCRIPTS = BASE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from bootstrap_database import ensure_database

DB = BASE / "database" / "legislation.sqlite"
DATABASE_REBUILT = ensure_database()

@st.cache_data
def query(sql):
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con)

textes = query("SELECT * FROM textes")
scrutins = query("SELECT * FROM scrutins")
amendements = query("SELECT * FROM amendements")
acteurs = query("SELECT * FROM acteurs")
groupes = query("SELECT * FROM groupes")
votes = query("SELECT * FROM votes_individuels")
positions_groupes = query("SELECT * FROM positions_groupes")
actes = query("SELECT * FROM actes_reglementaires")
ind_textes = query("SELECT * FROM indicateurs_textes")
ind_acteurs = query("SELECT * FROM indicateurs_acteurs")
ind_groupes = query("SELECT * FROM indicateurs_groupes")
mobilisation = query("SELECT * FROM mobilisation")
timeline = query("SELECT * FROM chronologie_procedures")
application = query("SELECT * FROM application_textes_enrichie")
couverture = query("SELECT * FROM couverture_donnees")
imports = query("SELECT * FROM statut_imports")
sources = query("SELECT * FROM sources")

st.title("Qui vote quoi")
if DATABASE_REBUILT:
    st.success("La base de données a été reconstruite automatiquement depuis les fichiers CSV.")
st.caption("V8.1 · Votes, efficacité, chronologie, élus, groupes et application des lois")

with st.sidebar:
    niveaux = st.multiselect(
        "Niveau", sorted(textes.niveau.dropna().unique()),
        default=sorted(textes.niveau.dropna().unique())
    )
    institutions = st.multiselect(
        "Institution", sorted(textes.institution.dropna().unique()),
        default=sorted(textes.institution.dropna().unique())
    )
    themes = st.multiselect(
        "Thème", sorted(textes.theme.dropna().unique()),
        default=sorted(textes.theme.dropna().unique())
    )
    recherche = st.text_input("Recherche")

vue = textes[
    textes.niveau.isin(niveaux)
    & textes.institution.isin(institutions)
    & textes.theme.isin(themes)
].copy()

if recherche:
    needle = recherche.lower()
    vue = vue[
        vue.titre.str.lower().str.contains(needle, na=False)
        | vue.presentateur.str.lower().str.contains(needle, na=False)
        | vue.theme.str.lower().str.contains(needle, na=False)
    ]

total_scrutins = len(scrutins)
adoptes = int(scrutins.resultat.fillna("").str.lower().str.contains("adopt").sum())
amd_total = len(amendements)
amd_adoptes = int(amendements["sort"].fillna("").str.lower().str.contains("adopt").sum())

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Textes", len(textes))
m2.metric("Scrutins", total_scrutins)
m3.metric("Scrutins adoptés", adoptes)
m4.metric("Amendements recensés", amd_total)
m5.metric("Couverture moyenne", f"{couverture.couverture_pct.mean():.0f} %")

st.warning(
    "Les indicateurs ne couvrent que les données intégrées. "
    "Les fiches élus et groupes deviendront pleinement utiles après import des votes nominatifs."
)

tabs = st.tabs([
    "Synthèse","Qui vote quoi","Textes","Efficacité","Chronologie",
    "Mobilisation","Scrutins","Amendements","Élus","Groupes",
    "Application des lois","Qualité des données","Imports","Méthode","Sources"
])

with tabs[0]:
    c1,c2 = st.columns(2)
    with c1:
        resultats = scrutins.groupby("resultat", as_index=False).size()
        st.plotly_chart(px.pie(resultats, names="resultat", values="size", title="Résultats"), width="stretch")
    with c2:
        themes_count = textes.groupby("theme", as_index=False).size()
        st.plotly_chart(px.bar(themes_count, x="theme", y="size", text="size", title="Textes par thème"), width="stretch")
    st.dataframe(
        ind_textes[[
            "titre","institution","statut","duree_jours",
            "scrutins_recenses","taux_adoption_scrutins_pct",
            "amendements_recenses","taux_adoption_amendements_pct",
            "taux_application_pct","score_documentation_pct"
        ]],
        width="stretch", hide_index=True
    )

with tabs[1]:
    numeric = scrutins.dropna(subset=["pour","contre"]).copy()
    if numeric.empty:
        st.info("Aucun scrutin chiffré.")
    else:
        selected = st.selectbox(
            "Scrutin",
            numeric.scrutin_id.tolist(),
            format_func=lambda sid: numeric.loc[numeric.scrutin_id == sid, "objet"].iloc[0]
        )
        row = numeric[numeric.scrutin_id == selected].iloc[0]
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Pour", int(row["pour"]))
        c2.metric("Contre", int(row["contre"]))
        c3.metric("Abstentions", int(row["abstention"]))
        c4.metric("Participation", f"{row['participation_pct']:.1f} %")
        c5.metric("Clivage", row["niveau_clivage"])
        chart = pd.DataFrame({
            "Position":["Pour","Contre","Abstention"],
            "Voix":[row["pour"],row["contre"],row["abstention"]]
        })
        st.plotly_chart(px.bar(chart, x="Position", y="Voix", text="Voix"), width="stretch")
        if positions_groupes.empty:
            st.info("Les détails par groupe seront alimentés par les imports nominatifs.")

with tabs[2]:
    st.dataframe(vue, width="stretch", hide_index=True)

with tabs[3]:
    selection = st.selectbox("Texte", ind_textes.titre.sort_values(), key="eff_text")
    row = ind_textes[ind_textes.titre == selection].iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Durée", "N/D" if pd.isna(row.duree_jours) else f"{int(row.duree_jours)} jours")
    c2.metric("Scrutins adoptés", f"{int(row.scrutins_adoptes)}/{int(row.scrutins_recenses)}")
    c3.metric("Amendements adoptés", f"{int(row.amendements_adoptes)}/{int(row.amendements_recenses)}")
    c4.metric("Application", "N/D" if pd.isna(row.taux_application_pct) else f"{row.taux_application_pct:.1f} %")
    st.dataframe(ind_textes[ind_textes.titre == selection].T, width="stretch")

with tabs[4]:
    options = timeline.titre.dropna().unique().tolist()
    selected = st.selectbox("Texte", sorted(options), key="timeline_text")
    tl = timeline[timeline.titre == selected].copy()
    tl["date"] = pd.to_datetime(tl["date"], errors="coerce")
    st.dataframe(tl[["date","etape","statut","detail","institution"]], width="stretch", hide_index=True)
    if not tl.empty:
        fig = px.scatter(
            tl, x="date", y="etape", color="statut",
            hover_data=["detail","institution"],
            title="Chronologie observée"
        )
        st.plotly_chart(fig, width="stretch")

with tabs[5]:
    mob = mobilisation.merge(textes[["texte_id","titre","institution"]], on="texte_id", how="left")
    st.dataframe(mob, width="stretch", hide_index=True)
    chart = mob.dropna(subset=["indice_mobilisation"]).sort_values("indice_mobilisation")
    if not chart.empty:
        st.plotly_chart(
            px.bar(chart, x="indice_mobilisation", y="titre", orientation="h", text="indice_mobilisation"),
            width="stretch"
        )
    st.warning("Cet indice n'est pas une mesure du nombre réel d'heures travaillées.")

with tabs[6]:
    st.dataframe(scrutins, width="stretch", hide_index=True)

with tabs[7]:
    st.dataframe(amendements, width="stretch", hide_index=True)
    if len(amendements):
        stats = amendements.assign(
            adopte=amendements["sort"].fillna("").str.lower().str.contains("adopt")
        ).groupby(["institution","auteur"], as_index=False).agg(
            deposes=("amendement_id","count"), adoptes=("adopte","sum")
        )
        stats["taux_adoption_pct"] = (stats.adoptes / stats.deposes * 100).round(1)
        st.dataframe(stats, width="stretch", hide_index=True)

with tabs[8]:
    st.dataframe(ind_acteurs, width="stretch", hide_index=True)
    selected = st.selectbox("Acteur", ind_acteurs.nom.sort_values(), key="actor")
    actor = ind_acteurs[ind_acteurs.nom == selected].iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Votes exprimés", int(actor.votes_exprimes))
    c2.metric("Participation", "N/D" if pd.isna(actor.participation_pct) else f"{actor.participation_pct:.1f} %")
    c3.metric("Amendements déposés", int(actor.amendements_deposes))
    c4.metric("Taux d'adoption", "N/D" if pd.isna(actor.taux_adoption_amendements_pct) else f"{actor.taux_adoption_amendements_pct:.1f} %")
    st.caption(actor.qualite)

with tabs[9]:
    st.dataframe(ind_groupes, width="stretch", hide_index=True)
    if ind_groupes.scrutins_analyses.sum() == 0:
        st.info("Les indicateurs de groupe attendent les positions officielles par scrutin.")

with tabs[10]:
    st.dataframe(
        application[[
            "titre","institution","type_texte","statut",
            "decrets_attendus","decrets_publies","ecart_decrets",
            "taux_application_pct","statut_application","source_url"
        ]],
        width="stretch", hide_index=True
    )
    known = application.dropna(subset=["taux_application_pct"])
    if not known.empty:
        st.plotly_chart(
            px.bar(known, x="titre", y="taux_application_pct", text="taux_application_pct"),
            width="stretch"
        )

with tabs[11]:
    st.dataframe(couverture.sort_values("couverture_pct"), width="stretch", hide_index=True)
    st.plotly_chart(
        px.bar(
            couverture.sort_values("couverture_pct"),
            x="couverture_pct", y="titre", orientation="h",
            text="couverture_pct",
            labels={"couverture_pct":"Couverture (%)","titre":""}
        ),
        width="stretch"
    )

with tabs[12]:
    st.dataframe(imports, width="stretch", hide_index=True)

with tabs[13]:
    st.markdown("""
    - Les taux sont calculés uniquement sur les enregistrements présents.
    - Une absence de donnée n'est pas une absence d'activité.
    - L'indice de mobilisation ne mesure pas les heures réelles.
    - Le taux d'application exige de connaître les décrets attendus et publiés.
    - La discipline de groupe nécessite les votes nominatifs.
    - Les scores composites servent à la navigation, pas à classer moralement les élus.
    """)

with tabs[14]:
    st.dataframe(sources, width="stretch", hide_index=True)
