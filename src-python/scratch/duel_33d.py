#!/usr/bin/env python3
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
from tqdm import tqdm
from datetime import datetime

# Add project root
sys.path.append(os.getcwd())
from core.neural import ProphitNet

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("Duel33D")

def run_duel():
    data_path = "backend/data/mother_brain_omniscient_33.parquet"
    if not os.path.exists(data_path):
        logger.error(f"❌ 33D Manifold Data missing: {data_path}")
        return

    logger.info("🧪 [OMNISCIENT DUEL] Initializing Unified 33D Manifold...")
    df = pd.read_parquet(data_path)
    
    features = [
        'returns', 'volatility', 'momentum', 'rsi', 'volume_z',
        'fluid_phase', 'fluid_envelope', 'fluid_stability', 'fluid_esn_depth', 'fluid_dmd_forecast',
        'sig_liquidity_hole', 'sig_dragon', 'sig_snake', 'sig_typhoon_sanctuary',
        'sig_entropy_strategy', 'sig_reality_arbitrage', 'sig_stigmergy', 
        'sig_prophit_team', 'sig_kuramoto', 'sig_soros_loop', 'sig_minsky_moment',
        'regime_id', 'regime_intensity', 'fracture_idx', 'consensus_z', 'sector_drift',
        'astro_moon_illumination', 'astro_kp_index', 'astro_sunspot', 'astro_day_of_year',
        'astro_hour_of_day', 'astro_day_of_week', 'astro_moon_phase'
    ]

    # Assembly (Unified Pool)
    X, y = [], []
    seq_len = 60
    
    vals = df[features].values
    tars = df['target'].values
    
    for i in tqdm(range(seq_len, len(df)), desc="🧩 Assembling Unified 33D Sequences"):
        X.append(vals[i-seq_len:i])
        y.append(tars[i])
    
    X = torch.tensor(np.array(X, dtype=np.float32))
    y = torch.tensor(np.array(y, dtype=np.float32)).unsqueeze(1)
    
    dataset = TensorDataset(X, y)
    train_size = int(0.9 * len(dataset))
    train_ds, val_ds = random_split(dataset, [train_size, len(dataset)-train_size])
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    # Duel Brain
    model = ProphitNet(input_size=33, hidden_size=256, num_layers=3)
    optimizer = optim.Adam(model.parameters(), lr=0.0003)
    criterion = nn.BCEWithLogitsLoss()

    logger.info(f"🚀 DUEL START: 20 Epochs of Sovereignty...")
    for epoch in range(3):
        model.train()
        train_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/20", leave=False)
        for Xb, yb in pbar:
            optimizer.zero_grad()
            out = model(Xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")
        
        # Validation
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for Xb, yb in val_loader:
                out = model(Xb)
                pred = (torch.sigmoid(out) > 0.5).float()
                correct += (pred == yb).sum().item()
                total += yb.size(0)
        
        acc = correct/total
        logger.info(f"📍 Epoch {epoch+1} Complete: Loss={train_loss/len(train_loader):.4f} | Accuracy={acc:.2%}")
        
        if acc > 0.8642:
            logger.info(f"🏆 SOVEREIGN OVERTAKE! 33D [{acc:.2%}] has surpassed Sacred 13 [86.42%]")
            
            # --- [PERSISTENCE BRIDGE] ---
            save_path = "backend/models/champion_33d_candidate.pt"
            torch.save(model.state_dict(), save_path)
            logger.info(f"💾 33D SOVEREIGN WEIGHTS PERSISTED TO {save_path}")

if __name__ == "__main__":
    run_duel()
