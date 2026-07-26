import numpy as np
import matplotlib.pyplot as plt
from utils.airwindows_console import AirwindowsConsole
from utils.divine_math import DivineMath

def run_analog_audit():
    print("🏛️ Starting Forensic Analog Audit...")
    
    # 1. Generate 'Harsh' Digital Market Data (Noise + Spikes)
    np.random.seed(42)
    t = np.linspace(0, 10, 1000)
    # A base trend with high-frequency jitter and extreme 'Wick' spikes
    raw_signal = np.sin(t) + np.random.normal(0, 0.1, 1000)
    raw_signal[200] = 3.5  # Positive Spike
    raw_signal[500] = -4.2 # Negative Spike
    raw_signal[800:820] += np.random.normal(0, 0.5, 20) # Volatility burst
    
    # 2. Setup Airwindows Consoles
    console_la = AirwindowsConsole(flavor="consolela")
    console_9 = AirwindowsConsole(flavor="console9")
    
    processed_signal = []
    
    # 3. Process through the Analog Desk
    for s in raw_signal:
        # Step A: Channel In (SubTight)
        clean = console_la.apply_subtight(s)
        
        # Step B: Summing Bus (Golden Ratio Saturation)
        # We simulate a single-channel bus for the audit
        encoded = console_9.encode(clean)
        decoded = console_9.decode(encoded)
        
        # Step C: Master Desk (ClipOnly3 Limiter)
        final = console_9.master_desk(decoded)
        processed_signal.append(final)
    
    processed_signal = np.array(processed_signal)
    
    # 4. Analytics: Measure the 'Unshackling'
    raw_slew = np.abs(np.diff(raw_signal))
    proc_slew = np.abs(np.diff(processed_signal))
    
    harshness_reduction = (1.0 - (np.mean(proc_slew) / np.mean(raw_slew))) * 100
    max_spike_reduction = (1.0 - (np.max(np.abs(processed_signal)) / np.max(np.abs(raw_signal)))) * 100
    
    print(f"✅ Audit Complete.")
    print(f"📊 Harshness Reduction (Slew): {harshness_reduction:.2f}%")
    print(f"📊 Max Spike Dampening: {max_spike_reduction:.2f}%")
    
    # 5. Visualization (Terminal Plot or Data Summary)
    print("\n[ SIGNAL PREVIEW ]")
    print("Raw Range:     ", np.min(raw_signal), "to", np.max(raw_signal))
    print("Analog Range:  ", np.min(processed_signal), "to", np.max(processed_signal))
    
    if harshness_reduction > 30 and max_spike_reduction > 50:
        print("\n🏆 LEGENDARY POKEMON DETECTED: The Airwindows Engine is effectively unshackling the signal.")
    else:
        print("\n⚠️ Training needed. The signal is still too digital.")

if __name__ == "__main__":
    run_analog_audit()
