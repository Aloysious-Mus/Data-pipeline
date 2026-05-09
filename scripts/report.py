"""
Report Generator - Patent Analysis Pipeline
Generates:
  1. Console report (terminal output)
  2. JSON report   (Reports/patent_report.json)
  3. Clean CSVs    (Reports/clean_*.csv + top_*.csv + country_trends.csv)

Run with: python scripts/report.py
"""
import sqlite3
import os
import json
import pandas as pd
from datetime import datetime

DB_PATH     = os.path.join("data", "patents.db")
REPORTS_DIR = "Reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── DB helper ──────────────────────────────────────────────────────────────────
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ── Fetch all report data ──────────────────────────────────────────────────────
def fetch_report_data() -> dict:
    print("  Fetching data from database...")

    total_patents   = query("SELECT COUNT(*) AS n FROM patents").iloc[0, 0]
    total_inventors = query("SELECT COUNT(DISTINCT inventor_id) AS n FROM inventors").iloc[0, 0]
    total_companies = query("SELECT COUNT(DISTINCT company_id) AS n FROM assignees").iloc[0, 0]
    total_countries = query(
        "SELECT COUNT(DISTINCT country) AS n FROM inventors WHERE country IS NOT NULL AND country != ''"
    ).iloc[0, 0]

    top_inventors = query("""
        SELECT inventor_name AS name, COUNT(DISTINCT patent_id) AS patents
        FROM inventors
        WHERE inventor_name IS NOT NULL AND inventor_name != ''
        GROUP BY inventor_id, inventor_name
        ORDER BY patents DESC LIMIT 10
    """)

    top_companies = query("""
        SELECT company_name AS name, COUNT(DISTINCT patent_id) AS patents
        FROM assignees
        WHERE company_name IS NOT NULL AND company_name != ''
        GROUP BY company_id, company_name
        ORDER BY patents DESC LIMIT 10
    """)

    top_countries = query("""
        SELECT country, COUNT(DISTINCT patent_id) AS patents
        FROM inventors
        WHERE country IS NOT NULL AND country != ''
        GROUP BY country
        ORDER BY patents DESC LIMIT 10
    """)

    yearly_trend = query("""
        SELECT filing_year AS year, COUNT(*) AS patents
        FROM patents
        WHERE filing_year IS NOT NULL AND filing_year > 1900
        GROUP BY filing_year ORDER BY filing_year
    """)

    return {
        "total_patents":   int(total_patents),
        "total_inventors": int(total_inventors),
        "total_companies": int(total_companies),
        "total_countries": int(total_countries),
        "top_inventors":   top_inventors,
        "top_companies":   top_companies,
        "top_countries":   top_countries,
        "yearly_trend":    yearly_trend,
    }


# ── 1. Console Report ──────────────────────────────────────────────────────────
def print_console_report(data: dict) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    w = 58

    print("\n" + "=" * w)
    print(" PATENT INTELLIGENCE REPORT ".center(w))
    print(f" Generated: {now} ".center(w))
    print("=" * w)

    print("\n  SUMMARY")
    print(f"  {'Total Patents':<20}: {data['total_patents']:>12,}")
    print(f"  {'Total Inventors':<20}: {data['total_inventors']:>12,}")
    print(f"  {'Total Companies':<20}: {data['total_companies']:>12,}")
    print(f"  {'Total Countries':<20}: {data['total_countries']:>12,}")

    print(f"\n  TOP 10 INVENTORS")
    print(f"  {'Rank':<5} {'Name':<35} {'Patents':>8}")
    print(f"  {'-'*5} {'-'*35} {'-'*8}")
    for i, row in data["top_inventors"].iterrows():
        print(f"  {i+1:<5} {str(row['name'])[:35]:<35} {int(row['patents']):>8,}")

    print(f"\n  TOP 10 COMPANIES")
    print(f"  {'Rank':<5} {'Company':<35} {'Patents':>8}")
    print(f"  {'-'*5} {'-'*35} {'-'*8}")
    for i, row in data["top_companies"].iterrows():
        print(f"  {i+1:<5} {str(row['name'])[:35]:<35} {int(row['patents']):>8,}")

    print(f"\n  TOP 10 COUNTRIES")
    print(f"  {'Rank':<5} {'Country':<20} {'Patents':>10}")
    print(f"  {'-'*5} {'-'*20} {'-'*10}")
    for i, row in data["top_countries"].iterrows():
        print(f"  {i+1:<5} {str(row['country']):<20} {int(row['patents']):>10,}")

    print(f"\n  YEARLY TREND (last 10 years)")
    print(f"  {'Year':<6} {'Patents':>10}  {'Bar Chart'}")
    print(f"  {'-'*6} {'-'*10}  {'-'*20}")
    for _, row in data["yearly_trend"].tail(10).iterrows():
        bar = "█" * min(int(row["patents"]) // 50000, 25)
        print(f"  {int(row['year']):<6} {int(row['patents']):>10,}  {bar}")

    print("\n" + "=" * w)
    print(" END OF REPORT ".center(w))
    print("=" * w + "\n")


# ── 2. JSON Report ─────────────────────────────────────────────────────────────
def save_json_report(data: dict) -> None:
    total = max(1, data["total_patents"])

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_patents":   data["total_patents"],
            "total_inventors": data["total_inventors"],
            "total_companies": data["total_companies"],
            "total_countries": data["total_countries"],
        },
        "top_inventors": [
            {"rank": i+1, "name": row["name"], "patents": int(row["patents"])}
            for i, row in data["top_inventors"].iterrows()
        ],
        "top_companies": [
            {"rank": i+1, "name": row["name"], "patents": int(row["patents"])}
            for i, row in data["top_companies"].iterrows()
        ],
        "top_countries": [
            {
                "rank": i+1,
                "country": row["country"],
                "patents": int(row["patents"]),
                "share": round(int(row["patents"]) / total, 4)
            }
            for i, row in data["top_countries"].iterrows()
        ],
        "yearly_trend": [
            {"year": int(row["year"]), "patents": int(row["patents"])}
            for _, row in data["yearly_trend"].iterrows()
        ],
    }

    path = os.path.join(REPORTS_DIR, "patent_report.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved → {path}")


# ── 3. Clean CSV Files ─────────────────────────────────────────────────────────
def save_clean_csvs() -> None:

    # clean_patents.csv
    df = query("SELECT patent_id, title, filing_date, filing_year FROM patents")
    df.to_csv(os.path.join(REPORTS_DIR, "clean_patents.csv"), index=False)
    print(f"  Saved → clean_patents.csv    ({len(df):,} rows)")

    # clean_inventors.csv
    df = query("""
        SELECT inventor_id, inventor_name AS name, country
        FROM inventors
        WHERE inventor_name IS NOT NULL AND inventor_name != ''
    """)
    df.to_csv(os.path.join(REPORTS_DIR, "clean_inventors.csv"), index=False)
    print(f"  Saved → clean_inventors.csv  ({len(df):,} rows)")

    # clean_companies.csv
    df = query("""
        SELECT DISTINCT company_id, company_name AS name
        FROM assignees
        WHERE company_name IS NOT NULL AND company_name != ''
    """)
    df.to_csv(os.path.join(REPORTS_DIR, "clean_companies.csv"), index=False)
    print(f"  Saved → clean_companies.csv  ({len(df):,} rows)")

    # top_inventors.csv
    df = query("""
        SELECT inventor_name AS name, COUNT(DISTINCT patent_id) AS patents
        FROM inventors
        WHERE inventor_name IS NOT NULL AND inventor_name != ''
        GROUP BY inventor_id, inventor_name
        ORDER BY patents DESC LIMIT 100
    """)
    df.to_csv(os.path.join(REPORTS_DIR, "top_inventors.csv"), index=False)
    print(f"  Saved → top_inventors.csv    ({len(df):,} rows)")

    # top_companies.csv
    df = query("""
        SELECT company_name AS name, COUNT(DISTINCT patent_id) AS patents
        FROM assignees
        WHERE company_name IS NOT NULL AND company_name != ''
        GROUP BY company_id, company_name
        ORDER BY patents DESC LIMIT 100
    """)
    df.to_csv(os.path.join(REPORTS_DIR, "top_companies.csv"), index=False)
    print(f"  Saved → top_companies.csv    ({len(df):,} rows)")

    # country_trends.csv
    df = query("""
        SELECT i.country, p.filing_year AS year,
               COUNT(DISTINCT i.patent_id) AS patents
        FROM inventors i
        JOIN patents p ON i.patent_id = p.patent_id
        WHERE i.country IS NOT NULL AND i.country != ''
          AND p.filing_year IS NOT NULL
        GROUP BY i.country, p.filing_year
        ORDER BY i.country, p.filing_year
    """)
    df.to_csv(os.path.join(REPORTS_DIR, "country_trends.csv"), index=False)
    print(f"  Saved → country_trends.csv   ({len(df):,} rows)")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 58)
    print(" REPORT GENERATION ".center(58))
    print("=" * 58)

    print("\n[1/3] Fetching data...")
    data = fetch_report_data()

    print("\n[2/3] Console report:")
    print_console_report(data)

    print("[3/3] Saving JSON report...")
    save_json_report(data)

    print("\n[4/4] Saving clean CSV files...")
    save_clean_csvs()

    print("\n" + "=" * 58)
    print(" All reports generated successfully! ".center(58))
    print(f" Folder: Reports/ ".center(58))
    print("=" * 58 + "\n")


if __name__ == "__main__":
    main()