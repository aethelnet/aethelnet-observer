import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.neural import ProphitNet

def run_performance_duel():
    model_path = "backend/models/heavy_artillery.pt"
    meta_path = "backend/models/heavy_artillery_meta.json"
    data_path = "backend/data/mother_brain_omniscient_33.parquet"

    print("🏛️ Starting Sovereign Performance Duel: Reason vs. Reflex...")

    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        print("❌ Production model or meta not found.")
        return

    # 1. Load Metadata and Model
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    input_size = meta['input_size']
    feature_cols = meta['feature_cols']
    
    # Mapping for sig_grand_assembly_theprophitteam
    mapping = {'sig_grand_assembly_theprophitteam': 'sig_prophit_team'}
    updated_feature_cols = [mapping.get(c, c) for c in feature_cols]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ProphitNet(input_size=input_size, hidden_size=meta.get('hidden_size', 128))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    # 2. Load Data
    print(f"📚 Subsuming 33D Manifold Data...")
    df = pd.read_parquet(data_path)
    symbols = df['symbol'].unique()
    seq_len = 60
    results = []

    # Rat Hyperparameters (Scorpio Calibration)
    RAT_SENSITIVITY = 2.9
    RAT_MRS = 3.18 # Mean Reversion Strength

    for symbol in symbols:
        sdf = df[df['symbol'] == symbol].copy()
        if len(sdf) < seq_len + 10: continue

        # --- MONARCH (REASON) EVALUATION ---
        data_vals = sdf[updated_feature_cols].values
        target_vals = sdf['target'].values
        
        X_monarch = []
        y_monarch = []
        for i in range(seq_len, len(sdf)):
            X_monarch.append(data_vals[i-seq_len:i])
            y_monarch.append(target_vals[i])
            
        X_tensor = torch.tensor(np.array(X_monarch, dtype=np.float32)).to(device)
        y_tensor = torch.tensor(np.array(y_monarch, dtype=np.float32)).unsqueeze(1).to(device)
        
        with torch.no_grad():
            outputs = model(X_tensor)
            monarch_probs = torch.sigmoid(outputs)
            monarch_acc = (1.0 - torch.abs(monarch_probs - y_tensor)).mean().item()

        # --- RAT (REFLEX) EVALUATION ---
        # The Rat fires on Panic Wicks (Volatility Sigma) or Z-Score extremes
        sdf['returns'] = sdf['close'].pct_change()
        sdf['volatility'] = sdf['returns'].rolling(30).std()
        sdf['sigma'] = (sdf['returns'].abs() / (sdf['volatility'] + 1e-9))
        
        rat_hits = 0
        rat_correct = 0
        monarch_local_correct = 0
        
        # Audit indices (starting after seq_len to align with Monarch)
        for i in range(seq_len, len(sdf)):
            row = sdf.iloc[i]
            target = row['target']
            
            # 1. Check Scorpio Sting (Sigma Reversal)
            sigma = row['sigma']
            z_score = row['consensus_z'] if 'consensus_z' in sdf.columns else 0.0
            
            rat_signal = 0 # 0: None, 1: Buy, -1: Sell
            
            if sigma > RAT_SENSITIVITY:
                # Panic Reversal
                rat_signal = -1 if row['returns'] > 0 else 1
            elif abs(z_score) > RAT_MRS:
                # High-Intensity Reversion
                rat_signal = -1 if z_score > 0 else 1
                
            if rat_signal != 0:
                rat_hits += 1
                # Accuracy: Did signal direction match target?
                # Target > 0.5 is UP, < 0.5 is DOWN
                is_correct = (rat_signal > 0 and target > 0.5) or (rat_signal < 0 and target < 0.5)
                if is_correct:
                    rat_correct += 1
                
                # Check how the Monarch did at this SAME timestamp
                idx_in_val = i - seq_len
                m_prob = monarch_probs[idx_in_val].item()
                m_correct = (m_prob > 0.5 and target > 0.5) or (m_prob < 0.5 and target < 0.5)
                if m_correct:
                    monarch_local_correct += 1

        rat_precision = rat_correct / rat_hits if rat_hits > 0 else 0.0
        monarch_local_acc = monarch_local_correct / rat_hits if rat_hits > 0 else 0.0

        results.append({
            'symbol': symbol,
            'monarch_global': monarch_acc,
            'rat_precision': rat_precision,
            'monarch_local': monarch_local_acc,
            'stings': rat_hits
        })

    # 3. Present Duel Results
    duel_df = pd.DataFrame(results).sort_values(by='rat_precision', ascending=False)
    
    print("\n⚔️  THE SOVEREIGN DUEL: REFLEX vs. REASON")
    print("-" * 75)
    print(f"{'SYMBOL':<10} | {'MONARCH_GLOBAL':<15} | {'RAT_STING_ACC':<15} | {'MONARCH_LOCAL':<15} | {'STINGS':<5}")
    print("-" * 75)
    for _, row in duel_df.iterrows():
        # Highlight where Rat outperforms Monarch in high-chaos
        winning = "👑 RAT" if row['rat_precision'] > row['monarch_local'] else "🏛️ MONARCH"
        print(f"{row['symbol']:<10} | {row['monarch_global']:<15.2%} | {row['rat_precision']:<15.2%} | {row['monarch_local']:<15.2%} | {row['stings']:<5} -> {winning}")
    print("-" * 75)
    
    report_path = "reports/reflex_vs_reason_duel.json"
    duel_df.to_json(report_path, orient='records', indent=2)
    print(f"\n📑 Duel report incinerated into {report_path}")

if __name__ == "__main__":
    run_performance_duel()
