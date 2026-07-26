import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.neural import ProphitNet

def run_fidelity_audit():
    model_path = "backend/models/heavy_artillery.pt"
    meta_path = "backend/models/heavy_artillery_meta.json"
    data_path = "backend/data/mother_brain_omniscient_33.parquet"

    print("🏛️ Starting Sovereign Fidelity Audit...")

    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        print("❌ Production model or meta not found.")
        return

    # 1. Load Metadata and Model
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    input_size = meta['input_size']
    hidden_size = meta.get('hidden_size', 128)
    num_layers = meta.get('num_layers', 3)
    feature_cols = meta['feature_cols']
    
    print(f"🧠 Loading {input_size}D Champion: {meta['version']} (Baseline: {meta['validation_accuracy']:.2%})")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ProphitNet(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    # 2. Load Data
    print(f"📚 Loading Manifold Data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    # Feature Name Mapping (Compatibility Layer)
    mapping = {
        'sig_grand_assembly_theprophitteam': 'sig_prophit_team'
    }
    updated_feature_cols = [mapping.get(c, c) for c in feature_cols]
    
    symbols = df['symbol'].unique()
    seq_len = 60
    results = []

    print(f"🔎 Auditing {len(symbols)} symbols...")

    for symbol in symbols:
        # Filter for this symbol
        sdf = df[df['symbol'] == symbol]
        
        if len(sdf) < seq_len + 10:
            print(f"⚠️  Skipping {symbol}: Insufficient samples ({len(sdf)})")
            continue

        # Prepare features
        try:
            data_vals = sdf[updated_feature_cols].values
        except KeyError as e:
            print(f"❌ Column missing for {symbol}: {e}")
            continue
        target_vals = sdf['target'].values
        
        X, y = [], []
        for i in range(seq_len, len(sdf)):
            X.append(data_vals[i-seq_len:i])
            y.append(target_vals[i])
            
        X = torch.tensor(np.array(X, dtype=np.float32)).to(device)
        y = torch.tensor(np.array(y, dtype=np.float32)).unsqueeze(1).to(device)
        
        # Inference
        with torch.no_grad():
            outputs = model(X)
            probs = torch.sigmoid(outputs)
            
            # Simple binary accuracy for auditing (Target 0.5 threshold)
            # Or Distance-based alignment like the trainer
            alignment = (1.0 - torch.abs(probs - y)).mean().item()
            
        results.append({
            'symbol': symbol,
            'accuracy': alignment,
            'samples': len(X)
        })

    # 3. Present Results
    audit_df = pd.DataFrame(results).sort_values(by='accuracy', ascending=False)
    
    print("\n🏆 LEADERBOARD OF FIDELITY (The Sovereign Sieve)")
    print("-" * 50)
    print(f"{'SYMBOL':<10} | {'ACCURACY':<10} | {'SAMPLES':<10}")
    print("-" * 50)
    for _, row in audit_df.iterrows():
        color = "✅" if row['accuracy'] >= 0.85 else "⚠️ " if row['accuracy'] >= 0.80 else "❌"
        print(f"{row['symbol']:<10} | {row['accuracy']:<10.2%} | {row['samples']:<10} {color}")
    print("-" * 50)
    
    # Save Report
    report_path = "reports/symbol_fidelity_audit.json"
    os.makedirs("reports", exist_ok=True)
    audit_df.to_json(report_path, orient='records', indent=2)
    print(f"\n📑 Detailed audit report saved to {report_path}")

if __name__ == "__main__":
    run_fidelity_audit()
