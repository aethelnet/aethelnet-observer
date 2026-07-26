#!/usr/bin/env python3
import time
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root
sys.path.append(os.getcwd())

from services.brain_full import get_engine
from core.failsafe import PanicSwitch

def clear_screen():
    print("\033[H\033[J", end="")

def run_watchtower():
    engine = get_engine()
    evolution_path = "backend/models/sovereign_evolution.json"
    
    while True:
        clear_screen()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_panic = PanicSwitch.is_active()
        
        # Pull Evolution Progress
        evo_text = "Evolution: 🌫️  IDLE"
        if os.path.exists(evolution_path):
            try:
                import json
                with open(evolution_path) as f:
                    evo = json.load(f)
                    epoch = evo.get('epoch', 0)
                    total = evo.get('total_epochs', 100)
                    acc = evo.get('current_accuracy', 0.0)
                    best = evo.get('best_accuracy_so_far', 0.85)
                    loss = evo.get('loss', 0.0)
                    
                    progress = (epoch / total) * 20
                    bar = "█" * int(progress) + "░" * (20 - int(progress))
                    evo_text = f"Monarch Evolution: [{bar}] {epoch}/{total} | Acc: {acc:.2%} (Target: >{best:.2%}) | Loss: {loss:.4f}"
            except: pass

        print(f"🏛️  SOVEREIGN WATCHTOWER | {now}")
        print(f"Status: {'🛑 PANIC_ACTIVE' if is_panic else '🛡️  OPERATIONAL'}")
        print(evo_text)
        print("-" * 60)
        
        # Pull Symbol States
        # Note: We access the internal states from BrainEngine
        states = engine.states
        
        if not states:
            print("\n⏳ Waiting for first 33D Manifold Pulse...")
        else:
            data = []
            for symbol, state in states.items():
                if symbol == "GLOBAL": continue # Skip metadata keys
                
                sync_score = state.get('last_sync_score', 0.0)
                ml_prob = state.get('last_ml_prob', 0.5)
                intensity = state.get('last_neural_signal', 0.0)
                
                # Visual Indicator for Sync
                # 0.90+ is structural persistence
                sync_vis = "💎" if sync_score >= 0.90 else "🌊" if sync_score >= 0.70 else "🌫️"
                
                data.append({
                    "Symbol": symbol,
                    "Sync": f"{sync_score:.2f} {sync_vis}",
                    "Conviction": f"{(abs(ml_prob - 0.5) * 200):.1f}%",
                    "Intensity": f"{intensity:.2f}",
                    "Status": "STRIKING" if intensity > 4.0 and sync_score > 0.8 else "OBSERVING"
                })
            
            df = pd.DataFrame(data)
            print(df.to_string(index=False))
        
        print("-" * 60)
        print("CTRL+C to return to the Void.")
        time.sleep(5)

if __name__ == "__main__":
    try:
        run_watchtower()
    except KeyboardInterrupt:
        print("\n\n🛡️ Watchtower Deactivated. The Monarch continues the hunt.")
