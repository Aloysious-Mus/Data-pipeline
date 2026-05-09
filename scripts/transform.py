"""
Transform phase: Clean, merge, and enrich extracted patent data.
"""
import pandas as pd


def transform_patents(patents_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize patent records."""
    print("Transforming patents...")

    df = patents_df.copy()

    # Drop rows missing critical fields
    df = df.dropna(subset=['patent_id', 'title'])

    # Normalize patent_id
    df['patent_id'] = df['patent_id'].str.strip()

    # Parse and normalize filing date
    df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
    df['filing_year'] = df['filing_year'] = df['filing_date'].dt.year

    # Clean title
    df['title'] = df['title'].str.strip().str.title()

    # Deduplicate
    df = df.drop_duplicates(subset=['patent_id'])

    print(f"  {len(df):,} patents after transformation")
    return df


def transform_abstracts(abstracts_df: pd.DataFrame) -> pd.DataFrame:
    """Clean patent abstracts."""
    print("Transforming abstracts...")

    df = abstracts_df.copy()

    df = df.dropna(subset=['patent_id', 'abstract'])
    df['patent_id'] = df['patent_id'].str.strip()
    df['abstract'] = df['abstract'].str.strip()

    # Remove empty strings after stripping
    df = df[df['abstract'].str.len() > 0]

    # Deduplicate (keep first abstract per patent)
    df = df.drop_duplicates(subset=['patent_id'])

    print(f"  {len(df):,} abstracts after transformation")
    return df


def transform_inventors(inventors_df: pd.DataFrame, locations_df: pd.DataFrame) -> pd.DataFrame:
    """Clean inventors and attach country via location join."""
    print("Transforming inventors...")

    inv = inventors_df.copy()
    loc = locations_df.copy()

    # Normalize keys
    inv['patent_id'] = inv['patent_id'].str.strip()
    inv['inventor_id'] = inv['inventor_id'].str.strip()
    inv['location_id'] = inv['location_id'].str.strip()
    loc['location_id'] = loc['location_id'].str.strip()

    # Build full name
    inv['first_name'] = inv['disambig_inventor_name_first'].fillna('').str.strip()
    inv['last_name'] = inv['disambig_inventor_name_last'].fillna('').str.strip()
    inv['inventor_name'] = (inv['first_name'] + ' ' + inv['last_name']).str.strip()

    # Drop rows with no usable name
    inv = inv[inv['inventor_name'].str.len() > 0]

    # Join location → country
    inv = inv.merge(loc, on='location_id', how='left')

    # Keep only relevant columns
    inv = inv[['patent_id', 'inventor_id', 'inventor_name', 'location_id', 'country']]

    print(f"  {len(inv):,} inventor records after transformation")
    return inv


def transform_assignees(assignees_df: pd.DataFrame) -> pd.DataFrame:
    """Clean assignee / company records."""
    print("Transforming assignees...")

    df = assignees_df.copy()

    df = df.dropna(subset=['patent_id', 'disambig_assignee_organization'])

    df['patent_id'] = df['patent_id'].str.strip()
    df['company_id'] = df['company_id'].str.strip()
    df['company_name'] = (
        df['disambig_assignee_organization']
        .str.strip()
        .str.title()
    )

    df = df.drop_duplicates(subset=['patent_id', 'company_id'])
    df = df[['patent_id', 'company_id', 'company_name']]

    print(f"  {len(df):,} assignee records after transformation")
    return df


def build_master_table(
    patents_df: pd.DataFrame,
    abstracts_df: pd.DataFrame,
    inventors_df: pd.DataFrame,
    assignees_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join all transformed tables into a single flat analytical table.
    One row per patent × inventor × assignee combination.
    """
    print("Building master table...")

    # Start with patents
    master = patents_df.merge(abstracts_df, on='patent_id', how='left')

    # Attach primary assignee (first company per patent)
    primary_assignee = assignees_df.drop_duplicates(subset=['patent_id'])
    master = master.merge(
        primary_assignee[['patent_id', 'company_id', 'company_name']],
        on='patent_id',
        how='left'
    )

    # Attach inventors (explodes rows — one per inventor)
    master = master.merge(inventors_df, on='patent_id', how='left')

    # Reorder columns for readability
    cols = [
        'patent_id', 'title', 'filing_date', 'filing_year',
        'abstract',
        'company_id', 'company_name',
        'inventor_id', 'inventor_name', 'country'
    ]
    master = master[[c for c in cols if c in master.columns]]

    print(f"  Master table: {len(master):,} rows, {master.shape[1]} columns")
    return master


def transform_all(raw: dict) -> dict:
    """
    Run all transform steps and return cleaned dataframes.

    Parameters
    ----------
    raw : dict
        Output from extract.extract_all() with keys:
        'patents', 'abstracts', 'inventors', 'assignees', 'locations'
    """
    print("=" * 50)
    print("TRANSFORM PHASE")
    print("=" * 50)

    patents   = transform_patents(raw['patents'])
    abstracts = transform_abstracts(raw['abstracts'])
    inventors = transform_inventors(raw['inventors'], raw['locations'])
    assignees = transform_assignees(raw['assignees'])
    master    = build_master_table(patents, abstracts, inventors, assignees)

    print("\nTransformation complete!")

    return {
        'patents':   patents,
        'abstracts': abstracts,
        'inventors': inventors,
        'assignees': assignees,
        'master':    master,
    }


if __name__ == "__main__":
    from extract import extract_all
    raw = extract_all()
    transformed = transform_all(raw)