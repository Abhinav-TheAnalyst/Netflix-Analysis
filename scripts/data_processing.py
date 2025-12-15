# scripts/data_processing.py
# Usage:
#   python scripts/data_processing.py raw/netflix1.csv processed/netflix_cleaned.csv

import pandas as pd
import sys
import os

def clean_netflix(input_path, output_path):
    df = pd.read_csv(input_path, encoding='utf-8', low_memory=False)

    # 1) Normalize column names
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # 2) Trim whitespace in string columns
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()

    # 3) Drop exact duplicates
    df = df.drop_duplicates()

    # 4) Drop rows with missing/empty title (if title exists)
    if 'title' in df.columns:
        df = df[~df['title'].isna() & (df['title'].str.len() > 0)]

    # 5) Parse date_added -> date_added_parsed, year_added, month_added
    if 'date_added' in df.columns:
        df['date_added_parsed'] = pd.to_datetime(df['date_added'], errors='coerce')
        df['year_added'] = df['date_added_parsed'].dt.year
        df['month_added'] = df['date_added_parsed'].dt.month

    # 6) Parse duration -> duration_int, duration_type
    if 'duration' in df.columns:
        def parse_duration(x):
            if pd.isna(x) or x == '':
                return pd.NA, pd.NA
            s = str(x).lower()
            num = ''.join(ch for ch in s if ch.isdigit())
            try:
                num = int(num)
            except:
                num = pd.NA
            if 'min' in s:
                t = 'minutes'
            elif 'season' in s:
                t = 'seasons'
            else:
                t = 'units'
            return num, t
        parsed = df['duration'].apply(parse_duration)
        df['duration_int'] = parsed.apply(lambda x: x[0])
        df['duration_type'] = parsed.apply(lambda x: x[1])

    # 7) cast_count
    if 'cast' in df.columns:
        df['cast_count'] = df['cast'].apply(lambda c: 0 if pd.isna(c) or c=='' else len([p for p in str(c).split(',') if p.strip()]))

    # 8) rating fill
    if 'rating' in df.columns:
        df['rating'] = df['rating'].replace({'nan': None}).fillna('Unknown')

    # 9) release_year numeric
    if 'release_year' in df.columns:
        df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce').astype('Int64')

    # 10) Reorder columns to useful order if present
    preferred = ['show_id','title','type','release_year','date_added_parsed','year_added','month_added','rating','duration','duration_int','duration_type','cast','cast_count','country','director','listed_in','description']
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    df = df[cols]

    # 11) Save cleaned CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned dataset to {output_path}. Shape: {df.shape}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scripts/data_processing.py raw/netflix1.csv processed/netflix_cleaned.csv")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]
    clean_netflix(inp, out)
