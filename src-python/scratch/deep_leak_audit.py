import pandas as pd
import numpy as np
import os
import torch

def deep_audit():
    parquet_path = "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/data/mother_brain_v11_sovereign_18d.parquet"
    df = pd.read_parquet(parquet_path)
    
    # Re-calculate target to be sure
    df['target'] = (df.groupby('symbol')['price'].shift(-1) > df['price']).astype(int)
    df = df.dropna()
    
    # Check if target is accidentally a column in the original parquet
    if 'target' in pd.read_parquet(parquet_path).columns:
        print("[!!!] WARNING: 'target' column already exists in Parquet file!")
    
    # Check for duplicate rows
    dupes = df.duplicated().sum()
    print(f"Duplicate rows in entire DF: {dupes}")
    
    # Check if price[t+1] is visible at time t
    # (This would be a massive bug in data manager)
    # We look for a feature that is 100% correlated with (price.shift(-1) > price)
    numeric_df = df.select_dtypes(include=[np.number])
    corrs = numeric_df.corr()['target'].abs().sort_values(ascending=False)
    print("\n[ABS CORRELATIONS]")
    print(corrs.head(10))

if __name__ == "__main__":
    deep_audit()
