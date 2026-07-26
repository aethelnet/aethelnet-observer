import pandas as pd
import numpy as np
import os
import xgboost as xgb

def biopsy():
    parquet_path = "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/data/mother_brain_v11_sovereign_18d.parquet"
    df = pd.read_parquet(parquet_path)
    
    # Replication of Academy logic
    CORE_DIMENSIONS = [
        "z_score", "alpha_flux", "dst_index", "tec_anomaly", 
        "flow_score", "phase_score", "returns", "volatility", 
        "momentum", "topology", "speed", "flare_score", 
        "bz", "seismic_energy", "kp_index", "solar_density", "rvi", "chrono_risk"
    ]
    
    df['target'] = (df.groupby('symbol')['price'].shift(-1) > df['price']).astype(int)
    df = df.dropna()
    
    split = int(len(df) * 0.8)
    train_df = df.iloc[:split]
    val_df = df.iloc[split:]
    
    # Train Soul
    soul_model = xgb.XGBClassifier(n_estimators=200, max_depth=6)
    soul_model.fit(train_df[CORE_DIMENSIONS], train_df['target'])
    
    # Get Preds
    train_preds = soul_model.predict_proba(train_df[CORE_DIMENSIONS])[:, 1]
    val_preds = soul_model.predict_proba(val_df[CORE_DIMENSIONS])[:, 1]
    
    # Audit
    train_corr = np.corrcoef(train_preds, train_df['target'])[0, 1]
    val_corr = np.corrcoef(val_preds, val_df['target'])[0, 1]
    
    print(f"\n[SOUL BIOPSY RESULTS]")
    print(f"[*] Training Correlation (Cheating): {train_corr:.4f}")
    print(f"[*] Validation Correlation (Reality): {val_corr:.4f}")
    
    if train_corr > 0.9 and val_corr < 0.2:
        print("\n[!!!] DIAGNOSIS: OVERPOWERED SOUL LEAK.")
        print("The Soul is so 'perfect' on training data that the Brain stops thinking.")

if __name__ == "__main__":
    biopsy()
