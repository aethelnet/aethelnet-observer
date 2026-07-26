import pandas as pd
import numpy as np
import os

def hunt():
    parquet_path = "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/data/mother_brain_v11_sovereign_18d.parquet"
    df = pd.read_parquet(parquet_path)
    
    # Target calculate
    df['target'] = (df.groupby('symbol')['price'].shift(-1) > df['price']).astype(int)
    df = df.dropna()
    
    numeric_df = df.select_dtypes(include=[np.number])
    
    print("Checking for identity leaks...")
    for col in numeric_df.columns:
        if col == 'target': continue
        
        # Check if feature at T is identical to target at T
        identity_match = (numeric_df[col] == numeric_df['target']).mean()
        if identity_match > 0.9:
            print(f"[!!!] IDENTITY LEAK: '{col}' matches target by {identity_match*100:.2f}%")
            
        # Check for shifted identity (maybe feature at T is target at T-1?)
        for shift in [-1, 1]:
            shifted_match = (numeric_df[col].shift(shift) == numeric_df['target']).mean()
            if shifted_match > 0.9:
                print(f"[!!!] SHIFTED LEAK ({shift}): '{col}' matches target by {shifted_match*100:.2f}%")

if __name__ == "__main__":
    hunt()
