
from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Qui vote quoi",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
groupes = query("SELECT * FROM groupes")
votes = query("SELECT * FROM votes_individuels")
positions_groupes = query("SELECT * FROM positions_groupes")
actes = query("SELECT * FROM actes_reglementaires")
ind_textes = query("SELECT * FROM indicateurs_textes")
ind_acteurs = query("SELECT * FROM indicateurs_acteurs")
ind_groupes = query("SELECT * FROM indicateurs_groupes")
mobilisation = query("SELECT * FROM mobilisation")
imports = query("SELECT * FROM statut_imports")
sources = query("SELECT * FROM sources")

st.title("Qui vote quoi")
st.caption("V5 · Votes, amendements, efficacité, mobilisation et application des textes")

with st.sidebar:
    niveaux = st.multiselect(
        "Niveau",
        sorted(textes.niveau.dropna().unique()),
        default=sorted(textes.niveau.dropna().unique()),
    )
    institutions = st.multiselect(
        "Institution",
        sorted(textes.institution.dropna().unique()),
        default=sorted(textes.institution.dropna().unique()),
    )
    themes = st.multiselect(
        "Thème",
        sorted(textes.theme.dropna().unique()),
        default=sorted(textes.theme.dropna().unique()),
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
taux_adoption = adoptes / total_scrutins * 100 if total_scrutins else 0
amd_total = len(amendements)
amd_adoptes = int(amendements["sort"].fillna("").str.lower().str.contains("adopt").sum())
taux_amd = amd_adoptes / amd_total * 100 if amd_total else 0

m1,m2,m3,m4 = st.columns(4)
m1.metric("Textes recensés", len(textes))
m2.metric("Scrutins adoptés", f"{adoptes}/{total_scrutins}")
m3.metric("Taux d'adoption des scrutins", f"{taux_adoption:.1f} %")
m4.metric("Taux d'adoption des amendements", f"{taux_amd:.1f} %")

st.warning(
    "Les indicateurs calculés portent uniquement sur les données actuellement intégrées. "
    "Ils ne représentent pas encore l'ensemble du Parlement français ou européen."
)

tabs = st.tabs([
    "Synthèse",
    "Qui vote quoi",
    "Textes",
    "Efficacité des textes",
    "Mobilisation",
    "Scrutins",
    "Amendements",
    "Élus",
    "Groupes",
    "Application des lois",
    "Imports",
    "Méthode",
    "Sources",
])

with tabs[0]:
    c1,c2 = st.columns(2)
    with c1:
        resultats = scrutins.groupby("resultat", as_index=False).size()
        st.plotly_chart(
            px.pie(resultats, names="resultat", values="size", title="Résultats des scrutins"),
            width="stretch",
        )
    with c2:
        themes_count = textes.groupby("theme", as_index=False).size()
        st.plotly_chart(
            px.bar(
                themes_count,
                x="theme",
                y="size",
                text="size",
                title="Textes par thème",
                labels={"theme":"","size":"Textes"},
            ),
            width="stretch",
        )

    st.subheader("Indicateurs par texte")
    st.dataframe(
        ind_textes[[
            "titre","institution","statut","duree_jours",
            "scrutins_recenses","taux_adoption_scrutins_pct",
            "amendements_recenses","taux_adoption_amendements_pct",
            "participation_moyenne_pct","clivage_moyen",
            "taux_application_pct","score_documentation_pct"
        ]],
        width="stretch",
        hide_index=True,
    )

with tabs[1]:
    st.subheader("Lecture d'un scrutin")
    numeric = scrutins.dropna(subset=["pour","contre"]).copy()
    if numeric.empty:
        st.info("Aucun scrutin chiffré disponible.")
    else:
        selected = st.selectbox(
            "Scrutin",
            numeric.scrutin_id.tolist(),
            format_func=lambda sid: numeric.loc[numeric.scrutin_id == sid, "objet"].iloc[0],
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
            "Voix":[row["pour"],row["contre"],row["abstention"]],
        })
        st.plotly_chart(
            px.bar(chart, x="Position", y="Voix", text="Voix"),
            width="stretch",
        )
        st.markdown(f"[Voir le scrutin officiel]({row['url_officielle']})")

        if positions_groupes.empty:
            st.info(
                "Les positions détaillées par groupe et les dissidences seront visibles "
                "dès l'import des votes nominatifs."
            )

with tabs[2]:
    st.dataframe(vue, width="stretch", hide_index=True)

with tabs[3]:
    selection = st.selectbox("Texte analysé", ind_textes.titre.sort_values())
    row = ind_textes[ind_textes.titre == selection].iloc[0]

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Durée observée", "N/D" if pd.isna(row.duree_jours) else f"{int(row.duree_jours)} jours")
    c2.metric("Scrutins adoptés", f"{int(row.scrutins_adoptes)}/{int(row.scrutins_recenses)}")
    c3.metric(
        "Amendements adoptés",
        f"{int(row.amendements_adoptes)}/{int(row.amendements_recenses)}"
    )
    c4.metric(
        "Application",
        "N/D" if pd.isna(row.taux_application_pct) else f"{row.taux_application_pct:.1f} %"
    )

    st.dataframe(
        ind_textes[ind_textes.titre == selection].T,
        width="stretch",
        hide_index=False,
    )
    st.caption(
        "L'efficacité ne se résume pas au taux d'adoption. "
        "Un amendement d'opposition peut être utile même s'il est rejeté."
    )

with tabs[4]:
    mob = mobilisation.merge(
        textes[["texte_id","titre","institution"]],
        on="texte_id",
        how="left",
    )
    st.dataframe(
        mob[[
            "titre","institution","duree_jours","nombre_lectures",
            "reunions_commission","seances_publiques",
            "amendements_deposes","indice_mobilisation","note"
        ]],
        width="stretch",
        hide_index=True,
    )

    chart = mob.dropna(subset=["indice_mobilisation"]).sort_values("indice_mobilisation")
    if not chart.empty:
        st.plotly_chart(
            px.bar(
                chart,
                x="indice_mobilisation",
                y="titre",
                orientation="h",
                text="indice_mobilisation",
                labels={"indice_mobilisation":"Indice de mobilisation","titre":""},
            ),
            width="stretch",
        )

    st.warning(
        "L'indice de mobilisation n'est pas un nombre d'heures travaillées. "
        "Il combine lectures, réunions, séances et amendements documentés."
    )

with tabs[5]:
    st.dataframe(scrutins, width="stretch", hide_index=True)

with tabs[6]:
    st.dataframe(amendements, width="stretch", hide_index=True)
    if len(amendements):
        stats = amendements.assign(
            adopte=amendements["sort"].fillna("").str.lower().str.contains("adopt")
        ).groupby(["institution","auteur"], as_index=False).agg(
            deposes=("amendement_id","count"),
            adoptes=("adopte","sum"),
        )
        stats["taux_adoption_pct"] = (stats.adoptes / stats.deposes * 100).round(1)
        st.subheader("Efficacité observée des amendements")
        st.dataframe(stats, width="stretch", hide_index=True)

with tabs[7]:
    st.dataframe(acteurs, width="stretch", hide_index=True)
    if ind_acteurs.empty:
        st.info(
            "Les taux de participation, discipline, dissidence et adoption par élu "
            "seront calculés après import des votes nominatifs et amendements complets."
        )
    else:
        st.dataframe(ind_acteurs, width="stretch", hide_index=True)

with tabs[8]:
    st.dataframe(groupes, width="stretch", hide_index=True)
    if ind_groupes.empty:
        st.info(
            "Les indicateurs de discipline et d'efficacité par groupe "
            "seront calculés après import des positions individuelles."
        )
    else:
        st.dataframe(ind_groupes, width="stretch", hide_index=True)

with tabs[9]:
    application = query("SELECT * FROM application_textes")
    application = application.merge(
        textes[["texte_id","titre","institution"]],
        on="texte_id",
        how="left",
    )
    st.dataframe(
        application[[
            "titre","institution","decrets_attendus","decrets_publies",
            "taux_application_pct","statut_application","source_url"
        ]],
        width="stretch",
        hide_index=True,
    )

with tabs[10]:
    st.dataframe(imports, width="stretch", hide_index=True)
    st.markdown("""
    **Priorités**
    1. votes nominatifs de l'Assemblée nationale ;
    2. analyses par groupe du Sénat ;
    3. amendements complets ;
    4. votes du Parlement européen ;
    5. décrets d'application via Légifrance.
    """)

with tabs[11]:
    st.markdown("""
    ### Définitions

    - **Taux d'adoption d'un scrutin** : scrutins marqués adoptés / scrutins recensés.
    - **Taux d'adoption des amendements** : amendements adoptés / amendements recensés.
    - **Participation** : votants / effectif théorique de l'assemblée lorsque celui-ci est connu.
    - **Discipline de groupe** : part des votants alignés avec la position majoritaire du groupe.
    - **Dissidence** : position individuelle différente de la majorité du groupe.
    - **Indice de mobilisation** : score descriptif construit à partir des données documentées.
    - **Taux d'application** : décrets publiés / décrets attendus.
    - Aucune note composite ne doit être assimilée à une mesure absolue de la qualité du travail parlementaire.
    """)

with tabs[12]:
    st.dataframe(sources, width="stretch", hide_index=True)
