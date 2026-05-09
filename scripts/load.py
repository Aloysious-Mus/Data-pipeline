import sqlite3, os, pandas as pd

DATA_DIR    = "data"
DB_PATH     = os.path.join(DATA_DIR, "patents.db")
SCHEMA_SQL  = os.path.join("sql", "schema.sql")
REPORTS_DIR = "Reports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def apply_schema(conn, schema_path=SCHEMA_SQL):
    if not os.path.exists(schema_path):
        print(f"  [WARN] schema.sql not found — skipping.")
        return
    with open(schema_path, "r") as fh:
        conn.executescript(fh.read())
    conn.commit()
    print("  Schema applied.")

def load_patents(conn, df):
    rows = df[['patent_id','title','filing_date','filing_year']].copy()
    rows['filing_date'] = rows['filing_date'].astype(str)
    rows.to_sql('patents', conn, if_exists='replace', index=False)
    print(f"  {len(rows):,} rows -> patents")

def load_abstracts(conn, df):
    df[['patent_id','abstract']].to_sql('abstracts', conn, if_exists='replace', index=False)
    print(f"  {len(df):,} rows -> abstracts")

def load_inventors(conn, df):
    cols = ['patent_id','inventor_id','inventor_name','location_id','country']
    df[[c for c in cols if c in df.columns]].to_sql('inventors', conn, if_exists='replace', index=False)
    print(f"  {len(df):,} rows -> inventors")

def load_assignees(conn, df):
    cols = ['patent_id','company_id','company_name']
    df[[c for c in cols if c in df.columns]].to_sql('assignees', conn, if_exists='replace', index=False)
    print(f"  {len(df):,} rows -> assignees")

def load_master(conn, df):
    df.copy().to_sql('master', conn, if_exists='replace', index=False)
    print(f"  {len(df):,} rows -> master")

def export_reports(transformed):
    for name in ["patents","inventors","assignees","master"]:
        d = transformed.get(name)
        if d is None: continue
        d.to_csv(os.path.join(REPORTS_DIR, f"{name}.csv"), index=False)
        print(f"  Wrote {len(d):,} rows -> Reports/{name}.csv")

def load_all(transformed, db_path=DB_PATH, export_csv=True):
    print("=" * 50)
    print("LOAD PHASE")
    print("=" * 50)
    conn = get_connection(db_path)
    try:
        apply_schema(conn)
        load_patents(conn,   transformed['patents'])
        load_abstracts(conn, transformed['abstracts'])
        load_inventors(conn, transformed['inventors'])
        load_assignees(conn, transformed['assignees'])
        load_master(conn,    transformed['master'])
        conn.commit()
        print(f"\n  All tables committed to {db_path}")
    except Exception as exc:
        conn.rollback()
        print(f"\n  [ERROR] {exc}")
        raise
    finally:
        conn.close()
    if export_csv:
        export_reports(transformed)
    print("\nLoad complete!")

if __name__ == "__main__":
    from scripts.extract import extract_all
    from scripts.transform import transform_all
    raw = extract_all()
    load_all(transform_all(raw))