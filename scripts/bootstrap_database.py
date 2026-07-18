
from pathlib import Path
import sqlite3
import pandas as pd

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

EXPECTED_TABLES = set(FILES)

def existing_tables() -> set[str]:
    if not DB.exists():
        return set()
    try:
        with sqlite3.connect(DB) as con:
            rows = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        return {row[0] for row in rows}
    except sqlite3.DatabaseError:
        return set()

def rebuild_database() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    temporary = DB.with_suffix(".sqlite.tmp")
    if temporary.exists():
        temporary.unlink()

    con = sqlite3.connect(temporary)
    try:
        for table, filename in FILES.items():
            path = DATA / filename
            if not path.exists():
                raise FileNotFoundError(f"Fichier source manquant : {path}")
            df = pd.read_csv(path)
            df.to_sql(table, con, index=False, if_exists="replace")

        con.execute("CREATE INDEX IF NOT EXISTS idx_textes_theme ON textes(theme)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_scrutins_texte ON scrutins(texte_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_amendements_texte ON amendements(texte_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_timeline_texte ON chronologie_procedures(texte_id)")
        con.commit()
    finally:
        con.close()

    temporary.replace(DB)

def ensure_database() -> bool:
    current = existing_tables()
    if EXPECTED_TABLES.issubset(current):
        return False
    rebuild_database()
    return True

if __name__ == "__main__":
    rebuilt = ensure_database()
    print(f"Base reconstruite : {rebuilt}")
    print(DB)
