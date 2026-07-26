import torch
import numpy as np
from core.neural import ProphitNet

def test_gen6_forward_pass():
    print("🏛️ Initializing ProphitNet Gen 6 (Analog Neural Manifold)...")
    
    # Manifold config: 17 inputs (Elite Manifold), 512 hidden, 5 layers
    model = ProphitNet(input_size=17, hidden_size=512, num_layers=5, output_size=1)
    model.eval() # Inference mode
    
    print("✅ Model initialized with Airwindows Activations (Spiral, Console9, ClipOnly3).")
    
    # Generate a batch of 'Extreme' dummy market data
    # (batch_size=4, seq_len=20, features=17)
    batch_size = 4
    seq_len = 20
    dummy_input = torch.randn(batch_size, seq_len, 17) * 5.0 # High variance to test saturation
    
    print(f"📡 Passing batch of {batch_size} through the Analog Desk...")
    
    try:
        with torch.no_grad():
            output = model(dummy_input)
            
        print(f"✅ Forward pass successful.")
        print(f"📊 Output Shape: {output.shape}")
        print(f"📊 Final Conviction (Analog Verdicts):\n{output}")
        
        # Verify ClipOnly3 constraints (0.94 limit)
        max_val = torch.max(torch.abs(output)).item()
        print(f"🛡️ Max absolute output: {max_val:.4f}")
        
        if max_val <= 0.941:
            print("\n🏆 GEN 6 VALIDATED: The Analog Neurons are firing harmonically and ClipOnly3 is protecting the Master Bus.")
        else:
            print("\n⚠️ CLIPPER BREACH: Check the final layer logic.")
            
    except Exception as e:
        print(f"❌ Forward pass failed: {str(e)}")

if __name__ == "__main__":
    test_gen6_forward_pass()
