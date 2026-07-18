
from pathlib import Path
import pandas as pd
import sqlite3

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DB = BASE / "database" / "legislation.sqlite"

FILES = {
    "textes":"textes.csv",
    "scrutins":"scrutins.csv",
    "amendements":"amendements.csv",
    "acteurs":"acteurs.csv",
    "votes_individuels":"votes_individuels.csv",
    "actes_reglementaires":"actes_reglementaires.csv",
    "sources":"sources.csv",
    "groupes":"groupes.csv",
    "positions_groupes":"positions_groupes.csv",
    "statut_imports":"statut_imports.csv",
    "procedures":"procedures.csv",
    "application_textes":"application_textes.csv",
    "application_textes_enrichie":"application_textes_enrichie.csv",
    "indicateurs_textes":"indicateurs_textes.csv",
    "indicateurs_acteurs":"indicateurs_acteurs.csv",
    "indicateurs_groupes":"indicateurs_groupes.csv",
    "mobilisation":"mobilisation.csv",
    "chronologie_procedures":"chronologie_procedures.csv",
    "couverture_donnees":"couverture_donnees.csv",
}

if DB.exists():
    DB.unlink()

con = sqlite3.connect(DB)
for table, filename in FILES.items():
    pd.read_csv(DATA / filename).to_sql(table, con, index=False, if_exists="replace")

con.execute("CREATE INDEX IF NOT EXISTS idx_textes_theme ON textes(theme)")
con.execute("CREATE INDEX IF NOT EXISTS idx_scrutins_texte ON scrutins(texte_id)")
con.execute("CREATE INDEX IF NOT EXISTS idx_amendements_texte ON amendements(texte_id)")
con.execute("CREATE INDEX IF NOT EXISTS idx_timeline_texte ON chronologie_procedures(texte_id)")
con.commit()
con.close()
print(DB)
