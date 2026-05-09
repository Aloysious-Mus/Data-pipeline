"""
compress_reports.py
Samples large Report CSVs down to GitHub-safe sizes (<100MB each).
Keeps the most meaningful rows for each file.

Run with: python compress_reports.py
"""
import os
import pandas as pd

REPORTS_DIR = "Reports"

def file_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)

def compress(filename: str, df: pd.DataFrame) -> None:
    path = os.path.join(REPORTS_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  Saved → {filename:<25} ({len(df):>10,} rows)  {file_mb(path):.1f} MB")

def main():
    print("=" * 60)
    print(" COMPRESSING REPORT FILES FOR GITHUB ".center(60))
    print("=" * 60)

    # ── clean_patents.csv — keep 500k rows ────────────────────────
    print("\nProcessing clean_patents.csv...")
    path = os.path.join(REPORTS_DIR, "clean_patents.csv")
    df = pd.read_csv(path, dtype=str)
    print(f"  Original: {len(df):,} rows  {file_mb(path):.1f} MB")
    df = df.dropna(subset=["title"]).drop_duplicates(subset=["patent_id"])
    df = df.sample(n=min(500_000, len(df)), random_state=42).sort_values("filing_year", ascending=False)
    compress("clean_patents.csv", df)

    # ── clean_inventors.csv — keep 500k rows ──────────────────────
    print("\nProcessing clean_inventors.csv...")
    path = os.path.join(REPORTS_DIR, "clean_inventors.csv")
    df = pd.read_csv(path, dtype=str)
    print(f"  Original: {len(df):,} rows  {file_mb(path):.1f} MB")
    df = df.dropna(subset=["name"]).drop_duplicates(subset=["inventor_id"])
    df = df.sample(n=min(500_000, len(df)), random_state=42)
    compress("clean_inventors.csv", df)

    # ── clean_companies.csv — already small, just clean it ────────
    print("\nProcessing clean_companies.csv...")
    path = os.path.join(REPORTS_DIR, "clean_companies.csv")
    df = pd.read_csv(path, dtype=str)
    print(f"  Original: {len(df):,} rows  {file_mb(path):.1f} MB")
    df = df.dropna(subset=["name"]).drop_duplicates(subset=["company_id"])
    compress("clean_companies.csv", df)

    # ── master.csv — keep 200k rows ───────────────────────────────
    print("\nProcessing master.csv...")
    path = os.path.join(REPORTS_DIR, "master.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        print(f"  Original: {len(df):,} rows  {file_mb(path):.1f} MB")
        df = df.sample(n=min(200_000, len(df)), random_state=42)
        compress("master.csv", df)
    else:
        print("  Skipped (not found)")

    # ── country_trends.csv — keep all (usually small) ─────────────
    print("\nProcessing country_trends.csv...")
    path = os.path.join(REPORTS_DIR, "country_trends.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        print(f"  Original: {len(df):,} rows  {file_mb(path):.1f} MB")
        compress("country_trends.csv", df)

    # ── top_inventors.csv / top_companies.csv — already small ─────
    for fname in ["top_inventors.csv", "top_companies.csv"]:
        path = os.path.join(REPORTS_DIR, fname)
        if os.path.exists(path):
            df = pd.read_csv(path, dtype=str)
            size = file_mb(path)
            print(f"\n  {fname} — {len(df):,} rows  {size:.2f} MB  (no change needed)")

    # ── patent_report.json — already small ────────────────────────
    path = os.path.join(REPORTS_DIR, "patent_report.json")
    if os.path.exists(path):
        size = file_mb(path)
        print(f"\n  patent_report.json — {size:.2f} MB  (no change needed)")

    # ── Final size check ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" FINAL FILE SIZES ".center(60))
    print("=" * 60)
    print(f"  {'File':<30} {'Size':>10}")
    print(f"  {'-'*30} {'-'*10}")
    for fname in sorted(os.listdir(REPORTS_DIR)):
        fpath = os.path.join(REPORTS_DIR, fname)
        size  = file_mb(fpath)
        flag  = " ⚠️  OVER LIMIT" if size > 95 else ""
        print(f"  {fname:<30} {size:>8.1f} MB{flag}")

    print("\nDone! Now run:")
    print("  git add Reports/")
    print("  git commit -m 'Add compressed report files'")
    print("  git push origin main")
    print("=" * 60)


if __name__ == "__main__":
    main()