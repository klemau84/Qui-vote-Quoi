
from pathlib import Path
import pandas as pd, sqlite3
BASE=Path(__file__).resolve().parents[1]
DB=BASE/'database'/'legislation.sqlite'
FILES={'textes':'textes.csv','scrutins':'scrutins.csv','amendements':'amendements.csv','acteurs':'acteurs.csv','votes_individuels':'votes_individuels.csv','actes_reglementaires':'actes_reglementaires.csv','sources':'sources.csv'}
if DB.exists(): DB.unlink()
con=sqlite3.connect(DB)
for table,file in FILES.items():
    pd.read_csv(BASE/'data'/file).to_sql(table,con,index=False,if_exists='replace')
con.execute('CREATE INDEX IF NOT EXISTS idx_textes_theme ON textes(theme)')
con.execute('CREATE INDEX IF NOT EXISTS idx_scrutins_texte ON scrutins(texte_id)')
con.commit(); con.close()
print(DB)
