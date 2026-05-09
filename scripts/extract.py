"""
Extract phase: Read raw TSV files and select only needed columns.
"""
import pandas as pd
import os

# Path configuration
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def find_assignee_file():
    """Find the assignee file regardless of spelling."""
    possible_names = [
        f"{DATA_DIR}/g_assignee_disambiguated.tsv",
        f"{DATA_DIR}/g_assigne_disambiguated.tsv"
    ]
    for name in possible_names:
        if os.path.exists(name):
            return name
    return f"{DATA_DIR}/g_assigne_disambiguated.tsv"  # Default to typo version


def extract_patents(filepath=f"{DATA_DIR}/g_patent.tsv"):
    """Extract patent data with only required columns."""
    print("Extracting patents...")
    
    columns = ['patent_id', 'patent_title', 'patent_date']
    
    df = pd.read_csv(
        filepath,
        sep='\t',
        usecols=columns,
        dtype={'patent_id': str},
        low_memory=False
    )
    
    df = df.rename(columns={
        'patent_title': 'title',
        'patent_date': 'filing_date'
    })
    
    print(f"  Loaded {len(df):,} patents")
    return df


def extract_abstracts(filepath=f"{DATA_DIR}/g_patent_abstract.tsv"):
    """Extract patent abstracts."""
    print("Extracting abstracts...")
    
    columns = ['patent_id', 'patent_abstract']
    
    df = pd.read_csv(
        filepath,
        sep='\t',
        usecols=columns,
        dtype={'patent_id': str},
        low_memory=False
    )
    
    df = df.rename(columns={'patent_abstract': 'abstract'})
    
    print(f"  Loaded {len(df):,} abstracts")
    return df


def extract_inventors(filepath=f"{DATA_DIR}/g_inventor_disambiguated.tsv"):
    """Extract inventor data with location IDs."""
    print("Extracting inventors...")
    
    columns = [
        'patent_id',
        'inventor_id',
        'disambig_inventor_name_first',
        'disambig_inventor_name_last',
        'location_id'
    ]
    
    df = pd.read_csv(
        filepath,
        sep='\t',
        usecols=columns,
        dtype={'patent_id': str, 'inventor_id': str, 'location_id': str},
        low_memory=False
    )
    
    print(f"  Loaded {len(df):,} inventor records")
    return df


def extract_assignees(filepath=None):
    """Extract assignee (company) data."""
    if filepath is None:
        filepath = find_assignee_file()
    
    print(f"Extracting companies from: {os.path.basename(filepath)}...")
    
    columns = [
        'patent_id',
        'assignee_id',
        'disambig_assignee_organization'
    ]
    
    df = pd.read_csv(
        filepath,
        sep='\t',
        usecols=columns,
        dtype={'patent_id': str, 'assignee_id': str},
        low_memory=False
    )
    
    df = df.rename(columns={'assignee_id': 'company_id'})
    
    print(f"  Loaded {len(df):,} company records")
    return df


def extract_locations(filepath=f"{DATA_DIR}/g_location_disambiguated.tsv"):
    """Extract location data for country information."""
    print("Extracting locations...")
    
    columns = ['location_id', 'disambig_country']
    
    df = pd.read_csv(
        filepath,
        sep='\t',
        usecols=columns,
        dtype={'location_id': str},
        low_memory=False
    )
    
    df = df.rename(columns={'disambig_country': 'country'})
    
    print(f"  Loaded {len(df):,} locations")
    return df


def extract_all():
    """Run all extract functions and return dataframes."""
    print("=" * 50)
    print("EXTRACT PHASE")
    print("=" * 50)
    
    patents_df = extract_patents()
    abstracts_df = extract_abstracts()
    inventors_df = extract_inventors()
    assignees_df = extract_assignees()
    locations_df = extract_locations()
    
    print("\nExtraction complete!")
    
    return {
        'patents': patents_df,
        'abstracts': abstracts_df,
        'inventors': inventors_df,
        'assignees': assignees_df,
        'locations': locations_df
    }


if __name__ == "__main__":
    data = extract_all()