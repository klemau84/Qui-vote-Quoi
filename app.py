
from pathlib import Path
import sqlite3, pandas as pd, plotly.express as px, streamlit as st
st.set_page_config(page_title="Observatoire législatif",page_icon="⚖️",layout="wide")
DB=Path(__file__).parent/"database"/"legislation.sqlite"
@st.cache_resource
def con(): return sqlite3.connect(DB,check_same_thread=False)
@st.cache_data
def q(sql): return pd.read_sql_query(sql,con())
textes=q("SELECT * FROM textes"); scrutins=q("SELECT * FROM scrutins"); amendements=q("SELECT * FROM amendements")
acteurs=q("SELECT * FROM acteurs"); votes=q("SELECT * FROM votes_individuels")
actes=q("SELECT * FROM actes_reglementaires"); sources=q("SELECT * FROM sources")
st.title("Observatoire législatif")
st.caption("V1 · France et Union européenne : textes, amendements, soutiens, oppositions et votes")
with st.sidebar:
    niveaux=st.multiselect("Niveau",sorted(textes.niveau.unique()),default=sorted(textes.niveau.unique()))
    institutions=st.multiselect("Institution",sorted(textes.institution.unique()),default=sorted(textes.institution.unique()))
    recherche=st.text_input("Recherche")
vue=textes[textes.niveau.isin(niveaux)&textes.institution.isin(institutions)].copy()
if recherche:
    x=recherche.lower()
    vue=vue[vue.titre.str.lower().str.contains(x,na=False)|vue.presentateur.str.lower().str.contains(x,na=False)|vue.theme.str.lower().str.contains(x,na=False)]
a,b,c,d=st.columns(4)
a.metric("Textes",len(textes)); b.metric("Scrutins",len(scrutins)); c.metric("Amendements",len(amendements)); d.metric("Votes individuels",len(votes))
st.info("Les lois et résolutions suivent un circuit parlementaire. Les décrets et arrêtés relèvent généralement du pouvoir exécutif et sont recensés séparément.")
tabs=st.tabs(["Textes","Fiche texte","Scrutins","Amendements","Votes individuels","Acteurs","Actes réglementaires","France / Europe","Méthode","Sources"])
with tabs[0]:
    st.dataframe(vue,width="stretch",hide_index=True)
with tabs[1]:
    if len(vue):
        titre=st.selectbox("Texte",vue.titre.sort_values())
        r=vue[vue.titre==titre].iloc[0]
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Institution",r.institution); c2.metric("Type",r.type_texte); c3.metric("Statut",r.statut); c4.metric("Thème",r.theme)
        st.markdown(f"## {r.titre}"); st.write(f"**Présentateur :** {r.presentateur}"); st.write(f"**Origine :** {r.origine}"); st.markdown(f"[Dossier officiel]({r.url_officielle})")
        st.subheader("Scrutins liés"); st.dataframe(scrutins[scrutins.texte_id==r.texte_id],width="stretch",hide_index=True)
        st.subheader("Amendements liés"); st.dataframe(amendements[amendements.texte_id==r.texte_id],width="stretch",hide_index=True)
with tabs[2]:
    st.dataframe(scrutins,width="stretch",hide_index=True)
    n=scrutins.dropna(subset=["pour","contre"])
    if len(n):
        m=n.melt(id_vars=["scrutin_id"],value_vars=["pour","contre","abstention"],var_name="position",value_name="voix")
        st.plotly_chart(px.bar(m,x="scrutin_id",y="voix",color="position",barmode="group"),width="stretch")
with tabs[3]: st.dataframe(amendements,width="stretch",hide_index=True)
with tabs[4]:
    st.warning("La structure est prête. Les votes individuels seront importés depuis les jeux officiels lors de la prochaine phase.") if votes.empty else st.dataframe(votes,width="stretch",hide_index=True)
with tabs[5]: st.dataframe(acteurs,width="stretch",hide_index=True)
with tabs[6]:
    st.info("L'import Légifrance ajoutera les décrets, arrêtés et textes d'application.") if actes.empty else st.dataframe(actes,width="stretch",hide_index=True)
with tabs[7]:
    s=textes.groupby(["niveau","institution","statut"],as_index=False).size()
    st.dataframe(s,width="stretch",hide_index=True); st.plotly_chart(px.bar(s,x="institution",y="size",color="statut",text="size"),width="stretch")
with tabs[8]:
    st.markdown("- **Présenter** : auteur d'une proposition ou Gouvernement pour un projet.\n- **Soutenir** : vote pour, cosignature ou amendement favorable.\n- **Combattre** : vote contre, motion de rejet ou amendement de suppression.\n- Les votes non publics ne permettent pas toujours une attribution individuelle.\n- Une directive doit être transposée ; un règlement est directement applicable.")
with tabs[9]: st.dataframe(sources,width="stretch",hide_index=True)
