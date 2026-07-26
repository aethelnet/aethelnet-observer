import pandas as pd
import numpy as np
import os

def audit():
    parquet_path = "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/data/mother_brain_v11_sovereign_18d.parquet"
    if not os.path.exists(parquet_path):
        print(f"Parquet not found at {parquet_path}")
        return
        
    df = pd.read_parquet(parquet_path)
    print(f"Auditing {len(df)} rows...")
    
    # Replicate target logic from Academy
    df['target'] = (df.groupby('symbol')['price'].shift(-1) > df['price']).astype(int)
    
    # Drop columns that are not features (strings etc)
    numeric_df = df.select_dtypes(include=[np.number])
    numeric_df = numeric_df.dropna()
    
    correlations = numeric_df.corr()['target'].sort_values(ascending=False)
    print("\n[TOP CORRELATIONS WITH TARGET]")
    print(correlations.head(20))
    
    # Check if any feature is IDENTICAL to target
    for col in numeric_df.columns:
        if col != 'target':
            match_pct = (numeric_df[col] == numeric_df['target']).mean()
            if match_pct > 0.95:
                print(f"\n[!!!] DETECTED LEAK: Feature '{col}' matches target by {match_pct*100:.2f}%!")

if __name__ == "__main__":
    audit()
