import torch
import torch.nn as nn
import math

class SpiralActivation(nn.Module):
    """
    Neural activation inspired by Airwindows 'Spiral'.
    Smooth, organic saturation: sin(x * |x|) / |x|
    """
    def forward(self, x):
        abs_x = torch.abs(x)
        # Avoid division by zero
        safe_abs_x = torch.clamp(abs_x, min=1e-12)
        return torch.sin(x * safe_abs_x) / safe_abs_x

class Console9Activation(nn.Module):
    """
    Neural activation inspired by Airwindows 'Console9'.
    Uses the Golden Ratio for divine scaling.
    """
    def __init__(self):
        super().__init__()
        self.phi = 0.618033988749895
        self.inv_phi = 1.618033988749895

    def forward(self, x):
        # Normalized input
        x_scaled = x * self.phi
        # PyTorch evaluates BOTH branches in torch.where, leading to NaN in log1p for negative numbers!
        safe_pos = torch.clamp(x_scaled, min=0.0, max=0.999)
        safe_neg = torch.clamp(x_scaled, min=-0.999, max=0.0)
        
        # Apply Golden Ratio curve safely
        return torch.where(
            x_scaled > 0,
            -torch.expm1(-torch.log1p(safe_pos) * self.inv_phi),
            torch.expm1(torch.log1p(safe_neg) * self.inv_phi)
        )

class ClipOnly3Layer(nn.Module):
    """
    Neural layer implementing the ClipOnly3 logic.
    Ensures the final output is analog-safe and within bounds.
    """
    def __init__(self, threshold=0.94):
        super().__init__()
        self.threshold = threshold
        
    def forward(self, x):
        # In a neural context, we treat each element independently 
        # as a 'sample' in a temporal sequence.
        # Dynamic slew compensation is hard in a parallel batch,
        # so we use a high-fidelity soft-clipper variant for training stability.
        return torch.clamp(x, -self.threshold, self.threshold)

class TopologicalLatentEncoder(nn.Module):
    """
    Compresses the massive expanded manifold (45D+) down to exactly 3 topological dimensions.
    Applies Airwindows Console9 encoding to preserve depth before the final wave collapse.
    """
    def __init__(self, input_dim=128):
        super().__init__()
        self.compressor = nn.Linear(input_dim, 3)
        self.console_encode = Console9Activation()
        
    def forward(self, x):
        latent_3d = self.compressor(x)
        encoded_3d = self.console_encode(latent_3d)
        return encoded_3d

class ProphitNet(nn.Module):
    """
    Gen 6: Sovereign Analog Neural Manifold.
    Powered by Airwindows-inspired activations and Golden Ratio scaling.
    """
    def __init__(self, input_size=44, hidden_size=512, num_layers=5, output_size=1):
        super(ProphitNet, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Input Normalization
        self.input_norm = nn.LayerNorm(input_size)
        
        # LSTM Layer (Temporal Core)
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.3)
        
        # Attention Head (Console9 Powered)
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, 128),
            Console9Activation(), # [GOLDEN RATIO]
            nn.Linear(128, 1),
            nn.Softmax(dim=1)
        )
        
        # LayerNorm after LSTM
        self.ln_out = nn.LayerNorm(hidden_size)
        
        # Topological Latent Space (3D)
        self.latent_encoder = TopologicalLatentEncoder(input_dim=hidden_size)
        
        # Output Head (The Waveform Collapse: 3D -> 1D)
        self.fc = nn.Sequential(
            nn.Linear(3, 16),
            SpiralActivation(), # [AIRWINDOWS SPIRAL]
            nn.Linear(16, output_size),
            ClipOnly3Layer()    # [AIRWINDOWS CLIPONLY3]
        )
        
    def forward(self, x):
        x = self.input_norm(x)
        lstm_out, _ = self.lstm(x)
        lstm_out = self.ln_out(lstm_out)
        
        attn_weights = self.attention(lstm_out)
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        # The 3D Latent Space Compression
        latent_vector = self.latent_encoder(context)
        
        # The Waveform Collapse
        prediction = self.fc(latent_vector)
        return prediction
