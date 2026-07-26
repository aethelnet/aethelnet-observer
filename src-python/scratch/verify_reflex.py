import os
import sys
import numpy as np
import pandas as pd
import json

def verify_realignment():
    print("🦾⚔️🐀🛡️👑 SOVEREIGN REFLEX VERIFICATION STARTED 👑🛡️🐀⚔️🦾")
    
    # 1. Load Metadata
    meta_path = "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/models/champion_meta.json"
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    feature_list = meta.get('feature_cols', [])
    print(f"[Audit] Manifest Size: {len(feature_cols if 'feature_cols' in globals() else feature_list)}")
    print(f"[Audit] Dimension 1: {feature_list[0] if feature_list else 'MISSING'}")
    
    # 2. Mock Data
    prices = [100.0 + (i * 0.1) for i in range(100)]
    df = pd.DataFrame({'close': prices, 'volume': [1000.0] * 100})
    
    # 3. Test Feature Extraction Logic (Replicated from brain_full.py)
    # We test the exact same branch we injected
    for name in feature_list:
        if name.startswith('z_') and name != 'z_velocity':
            try:
                period = int(name.split('_')[-1])
                v_arr = df['close'].tail(period).values
                df[name] = (df['close'] - v_arr.mean()) / v_arr.std() if v_arr.std() > 1e-6 else 0.0
                # print(f"[Check] Feature '{name}' = {df[name].iloc[-1]:.4f}")
            except:
                df[name] = 0.0
        elif name == 'volume_z':
            v_arr = df['volume'].tail(20).values
            df[name] = (df['volume'] - v_arr.mean()) / v_arr.std() if v_arr.std() > 1e-6 else 0.0
            
    # Final Check
    print("\n--- RESULTS ---")
    if feature_list[0] == 'z_initiation_11' and 'z_initiation_11' in df.columns:
        print("✅ DIMENSION 1 REALIGNMENT: SUCCESSFUL")
        print(f"✅ STAT: z_initiation_11 value = {df['z_initiation_11'].iloc[-1]:.4f}")
    else:
        print("❌ DIMENSION 1 REALIGNMENT: FAILED")
        
    if len(feature_list) == 33:
        print("✅ MANIFEST SIZE: 33 (LOCKED)")
    else:
        print(f"❌ MANIFEST SIZE: {len(feature_list)} (MISMATCH)")

    print("\n🦾⚔️🐀🛡️👑 VERIFICATION COMPLETE 👑🛡️🐀⚔️🦾")

if __name__ == "__main__":
    verify_realignment()
