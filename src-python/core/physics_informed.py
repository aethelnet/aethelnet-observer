import torch
import torch.nn as nn
import math

class DifferentiableEWMA(nn.Module):
    """
    Computes an Exponentially Weighted Moving Average (EWMA) in a differentiable way.
    The decay rate 'alpha' is learned.
    """
    def __init__(self, initial_span=14.0):
        super().__init__()
        # Initialize alpha based on the span: alpha = 2 / (span + 1)
        initial_alpha = 2.0 / (initial_span + 1.0)
        # We store alpha as an unbounded parameter and use sigmoid to keep it in (0, 1)
        # inverse sigmoid of initial_alpha: log(alpha / (1 - alpha))
        inv_sig = math.log(initial_alpha / (1.0 - initial_alpha))
        self.alpha_raw = nn.Parameter(torch.tensor(inv_sig))

    def forward(self, x):
        """
        x: (Batch, SequenceLength)
        Returns: EWMA of x with the same shape.
        """
        alpha = torch.sigmoid(self.alpha_raw)
        
        batch_size, seq_len = x.shape
        
        ewma_steps = [x[:, 0]]
        for t in range(1, seq_len):
            ewma_t = alpha * x[:, t] + (1 - alpha) * ewma_steps[-1]
            ewma_steps.append(ewma_t)
            
        ewma = torch.stack(ewma_steps, dim=1)
        return ewma

class DifferentiableZScore(nn.Module):
    """
    Computes a rolling Z-Score where the window span is learned by the neural network.
    """
    def __init__(self, initial_span=33.0):
        super().__init__()
        self.ewma_mu = DifferentiableEWMA(initial_span)
        # We use a separate EWMA for the squared values, allowing the network
        # to theoretically learn different memory lengths for mean vs variance!
        self.ewma_sq = DifferentiableEWMA(initial_span)

    def forward(self, x):
        # x: (Batch, SequenceLength)
        mu = self.ewma_mu(x)
        sq = self.ewma_sq(x.pow(2))
        
        # Variance = E[X^2] - (E[X])^2
        var = torch.clamp(sq - mu.pow(2), min=1e-8)
        std = torch.sqrt(var)
        
        return (x - mu) / std

class DifferentiableRSI(nn.Module):
    """
    Computes the Relative Strength Index (RSI) using differentiable EWMA.
    The length of the RSI is learned.
    """
    def __init__(self, initial_span=14.0):
        super().__init__()
        self.ewma_gain = DifferentiableEWMA(initial_span)
        self.ewma_loss = DifferentiableEWMA(initial_span)
        
    def forward(self, x):
        # Price diff
        diff = x - torch.roll(x, shifts=1, dims=1)
        # For the first element, diff is 0
        diff[:, 0] = 0.0
        
        # Positive gains and negative losses
        gain = torch.relu(diff)
        loss = torch.relu(-diff)
        
        avg_gain = self.ewma_gain(gain)
        avg_loss = self.ewma_loss(loss)
        
        # RS = avg_gain / avg_loss
        rs = avg_gain / torch.clamp(avg_loss, min=1e-8)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi

class DifferentiableEntropy(nn.Module):
    """
    Computes a rolling Shannon Entropy of price direction.
    Learns the optimal window size for measuring market chaos.
    """
    def __init__(self, initial_span=14.0):
        super().__init__()
        self.ewma = DifferentiableEWMA(initial_span)
        
    def forward(self, x):
        diff = x - torch.roll(x, shifts=1, dims=1)
        diff[:, 0] = 0.0
        
        # Soft probability of an 'up' tick
        p_up = torch.sigmoid(diff * 10.0) # Scale to make it sharper
        
        # Smooth the probability
        avg_p_up = self.ewma(p_up)
        avg_p_down = 1.0 - avg_p_up
        
        # Shannon Entropy
        safe_p_up = torch.clamp(avg_p_up, 1e-6, 1.0 - 1e-6)
        safe_p_down = torch.clamp(avg_p_down, 1e-6, 1.0 - 1e-6)
        
        entropy = -(safe_p_up * torch.log2(safe_p_up) + safe_p_down * torch.log2(safe_p_down))
        return entropy

class DifferentiablePhase(nn.Module):
    """
    Computes the market Phase angle (Trend vs Volatility).
    Learns the optimal lookback for phase shifts.
    """
    def __init__(self, initial_span=21.0):
        super().__init__()
        self.ewma_diff = DifferentiableEWMA(initial_span)
        self.ewma_abs = DifferentiableEWMA(initial_span)
        
    def forward(self, x):
        diff = x - torch.roll(x, shifts=1, dims=1)
        diff[:, 0] = 0.0
        
        smoothed_diff = self.ewma_diff(diff)
        smoothed_abs = self.ewma_abs(torch.abs(diff))
        
        phase = torch.atan2(smoothed_diff, torch.clamp(smoothed_abs, min=1e-6))
        return phase

class DifferentiableSorosLoop(nn.Module):
    """
    Misst die Reflexivität des Marktes. Wann treibt sich der Trend selbst in den Kollaps?
    """
    def __init__(self, initial_span=33.0):
        super().__init__()
        self.ewma = DifferentiableEWMA(initial_span)
        self.gravity_threshold = nn.Parameter(torch.tensor(2.0))

    def forward(self, price, momentum):
        baseline = self.ewma(price)
        stretch = price - baseline
        bubble_energy = stretch * momentum
        reflexivity = torch.tanh(bubble_energy / self.gravity_threshold)
        return reflexivity

class DifferentiableVolatilitySqueeze(nn.Module):
    """
    Misst die Kompression (Bollinger Band Width) als Vorbote einer Explosion.
    """
    def __init__(self, initial_span=21.0):
        super().__init__()
        self.ewma_mu = DifferentiableEWMA(initial_span)
        self.ewma_sq = DifferentiableEWMA(initial_span)
        self.ewma_long_sq = DifferentiableEWMA(initial_span * 3.0)
        
    def forward(self, x):
        mu = self.ewma_mu(x)
        sq = self.ewma_sq(x.pow(2))
        long_sq = self.ewma_long_sq(x.pow(2))
        
        var_short = torch.clamp(sq - mu.pow(2), min=1e-8)
        var_long = torch.clamp(long_sq - mu.pow(2), min=1e-8)
        
        # Squeeze Ratio
        squeeze = torch.sqrt(var_short) / torch.sqrt(var_long)
        return squeeze

class Console9Activation(nn.Module):
    """
    Topological compression using the Golden Ratio (Airwindows Console9 style).
    Expands the dynamic range and compresses softly to preserve 40D relationships.
    """
    def __init__(self):
        super().__init__()
        self.phi = 1.618033988749895
        
    def forward(self, x):
        # Soft analog clipping and topological preservation
        encoded = torch.sin(torch.clamp(x, -1.0, 1.0) * (math.pi / 2.0) * self.phi)
        decoded = torch.asin(torch.clamp(encoded / self.phi, -0.999, 0.999))
        return decoded
class DifferentiableOrderbookGravity(nn.Module):
    """
    Computes the gravitational pull of the orderbook (Bids vs Asks).
    Takes a tensor of orderbook depth profiles and learns the true center of mass.
    """
    def __init__(self, depth_levels=5):
        super().__init__()
        # Learnable weights for each depth level
        # A sell-wall at level 5 might have less immediate gravity than a wall at level 1
        self.level_weights = nn.Parameter(torch.ones(depth_levels))
        
    def forward(self, bids_volume, asks_volume):
        """
        bids_volume: (Batch, SeqLen, DepthLevels)
        asks_volume: (Batch, SeqLen, DepthLevels)
        Returns Orderbook Imbalance (Gravity) between -1.0 (Down) and 1.0 (Up)
        """
        # Apply learned depth weighting
        weights = torch.softmax(self.level_weights, dim=0)
        
        weighted_bids = torch.sum(bids_volume * weights, dim=-1)
        weighted_asks = torch.sum(asks_volume * weights, dim=-1)
        
        # Calculate imbalance: (Bids - Asks) / (Bids + Asks)
        # Positive = More Bids (Upward Gravity / Floor)
        # Negative = More Asks (Downward Gravity / Ceiling)
        total_liquidity = weighted_bids + weighted_asks
        imbalance = (weighted_bids - weighted_asks) / torch.clamp(total_liquidity, min=1e-8)
        
        return torch.tanh(imbalance * 2.0) # Scale and squash

class PhysicsManifold(nn.Module):
    """
    The Expansion Engine.
    Takes the 5 pure DNA signals and expands them into a 40D manifold
    using trainable physics formulas.
    """
    def __init__(self):
        super().__init__()
        # Suppose input features at index 0 is Price (or log returns).
        # We create a massive array of physics sensors to reach the 40D manifold
        # 1. Schwerkraft (Z-Scores)
        self.z_micro = DifferentiableZScore(initial_span=5.0)
        self.z_initiation = DifferentiableZScore(initial_span=11.0)
        self.z_fallen = DifferentiableZScore(initial_span=13.0)
        self.z_trinity = DifferentiableZScore(initial_span=33.0)
        self.z_macro = DifferentiableZScore(initial_span=55.0)
        self.z_foundation = DifferentiableZScore(initial_span=111.0)
        self.z_beast = DifferentiableZScore(initial_span=666.0)
        
        # 2. Beschleunigung (RSI)
        self.rsi_micro = DifferentiableRSI(initial_span=5.0)
        self.rsi_fast = DifferentiableRSI(initial_span=9.0)
        self.rsi_slow = DifferentiableRSI(initial_span=21.0)
        self.rsi_macro = DifferentiableRSI(initial_span=55.0)
        
        # 3. Chaos (Entropy)
        self.entropy_fast = DifferentiableEntropy(initial_span=9.0)
        self.entropy_slow = DifferentiableEntropy(initial_span=33.0)
        
        # 4. Phasenwinkel (Trend vs Volatility)
        self.phase_fast = DifferentiablePhase(initial_span=13.0)
        self.phase_slow = DifferentiablePhase(initial_span=55.0)
        
        # 5. Reflexivität (Soros Loops)
        self.soros_micro = DifferentiableSorosLoop(initial_span=13.0)
        self.soros_macro = DifferentiableSorosLoop(initial_span=55.0)
        
        # 6. Kompression (Volatility Squeeze)
        self.squeeze_fast = DifferentiableVolatilitySqueeze(initial_span=13.0)
        self.squeeze_slow = DifferentiableVolatilitySqueeze(initial_span=33.0)
        self.squeeze_beast = DifferentiableVolatilitySqueeze(initial_span=111.0)
        
        # Raw Momentum Scalers for different lookbacks
        self.mom_scale_1 = nn.Parameter(torch.tensor(1.0))
        self.mom_scale_3 = nn.Parameter(torch.tensor(1.618))
        self.mom_scale_7 = nn.Parameter(torch.tensor(2.618))
        self.mom_scale_13 = nn.Parameter(torch.tensor(4.236))

    def forward(self, x):
        """
        x shape: (Batch, SequenceLength, 5)
        We extract the primary signal (e.g., price or log return at index 0)
        to compute the physics derivatives.
        """
        primary_signal = x[:, :, 0] 
        
        z5 = self.z_micro(primary_signal).unsqueeze(-1)
        z11 = self.z_initiation(primary_signal).unsqueeze(-1)
        z13 = self.z_fallen(primary_signal).unsqueeze(-1)
        z33 = self.z_trinity(primary_signal).unsqueeze(-1)
        z55 = self.z_macro(primary_signal).unsqueeze(-1)
        z111 = self.z_foundation(primary_signal).unsqueeze(-1)
        z666 = self.z_beast(primary_signal).unsqueeze(-1)
        
        r5 = self.rsi_micro(primary_signal).unsqueeze(-1)
        r9 = self.rsi_fast(primary_signal).unsqueeze(-1)
        r21 = self.rsi_slow(primary_signal).unsqueeze(-1)
        r55 = self.rsi_macro(primary_signal).unsqueeze(-1)
        
        e9 = self.entropy_fast(primary_signal).unsqueeze(-1)
        e33 = self.entropy_slow(primary_signal).unsqueeze(-1)
        
        p13 = self.phase_fast(primary_signal).unsqueeze(-1)
        p55 = self.phase_slow(primary_signal).unsqueeze(-1)
        
        s13 = self.soros_micro(primary_signal, primary_signal - torch.roll(primary_signal, 1, 1)).unsqueeze(-1)
        s55 = self.soros_macro(primary_signal, primary_signal - torch.roll(primary_signal, 1, 1)).unsqueeze(-1)
        
        sq13 = self.squeeze_fast(primary_signal).unsqueeze(-1)
        sq33 = self.squeeze_slow(primary_signal).unsqueeze(-1)
        sq111 = self.squeeze_beast(primary_signal).unsqueeze(-1)
        
        m1 = ((primary_signal - torch.roll(primary_signal, 1, 1)) * self.mom_scale_1).unsqueeze(-1)
        m3 = ((primary_signal - torch.roll(primary_signal, 3, 1)) * self.mom_scale_3).unsqueeze(-1)
        m7 = ((primary_signal - torch.roll(primary_signal, 7, 1)) * self.mom_scale_7).unsqueeze(-1)
        m13 = ((primary_signal - torch.roll(primary_signal, 13, 1)) * self.mom_scale_13).unsqueeze(-1)
        
        # 4 raw DNA (stationary only) + 7 Z + 4 RSI + 2 Ent + 2 Phase + 2 Soros + 3 Squeeze + 4 Mom = 28 Physics Features
        # We drop index 0 (absolute price) to make the entire sequence strictly stationary.
        
        expanded = torch.cat([x[:, :, 1:], z5, z11, z13, z33, z55, z111, z666, r5, r9, r21, r55, e9, e33, p13, p55, s13, s55, sq13, sq33, sq111, m1, m3, m7, m13], dim=-1)
        
        return expanded

class Gen7ProphitNet(nn.Module):
    """
    Gen 7 Sovereign Architecture:
    The 40D (29D) Model dynamically learns its own feature engineering and compresses it using Console9.
    """
    def __init__(self, input_size=4, expanded_size=23, hidden_size=256, num_layers=3):
        super().__init__()
        # Input size is 4 (stationary raw), physics engine outputs 24 derived features = 28 total
        self.expanded_size = input_size + expanded_size
        
        # Layer 1: Physics Engine
        self.physics = PhysicsManifold()
        
        # Normalization over the expanded physics
        self.norm = nn.LayerNorm(self.expanded_size)
        
        # Layer 1.5: Console9 Topological Compression (40D -> 3D Latent)
        self.console9 = Console9Activation()
        self.latent_compressor = nn.Linear(self.expanded_size, 3)
        
        # Layer 2: Deep Pattern Recognition on the 3D topology
        self.lstm = nn.LSTM(3, hidden_size, num_layers, batch_first=True, dropout=0.3)
        
        # Layer 3: Output
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.GELU(),
            nn.Linear(64, 1)
        )
        
    def forward(self, x, return_physics=False):
        # 1. Expand the pure 5D DNA into the 34D physical manifold
        manifold = self.physics(x)
        manifold_norm = self.norm(manifold)
        
        # 1.5. Console9 Compression: Preserving the topology while forcing a 3D bottleneck
        latent_3d = self.latent_compressor(manifold_norm)
        latent_3d = self.console9(latent_3d)
        
        # 2. Extract deep temporal patterns
        lstm_out, _ = self.lstm(latent_3d)
        
        # 3. Predict the final target using the last time step
        pred = self.fc(lstm_out[:, -1, :])
        
        if return_physics:
            return pred, manifold[:, -1, :]
            
        return pred

class Gen8ProphitNet(nn.Module):
    """
    Gen 8 Sovereign Architecture (The Orderbook Gravity Upgrade):
    Ingests 4D Price Data + 10D Orderbook Data.
    Compresses Orderbook into a scalar 'Gravity' metric.
    Expands into physical manifold, squashes via Console9, and predicts.
    """
    def __init__(self, input_size=4, expanded_size=23, hidden_size=256, num_layers=3, orderbook_levels=5):
        super().__init__()
        # The Gravity Sensor
        self.orderbook_gravity = DifferentiableOrderbookGravity(depth_levels=orderbook_levels)
        
        # We append 1 dimension (Gravity) to the base input size
        self.expanded_size = input_size + 1 + expanded_size
        
        # Layer 1: Physics Engine
        self.physics = PhysicsManifold()
        
        # Normalization over the expanded physics
        self.norm = nn.LayerNorm(self.expanded_size)
        
        # Layer 1.5: Console9 Topological Compression (Manifold -> 3D Latent)
        self.console9 = Console9Activation()
        self.latent_compressor = nn.Linear(self.expanded_size, 3)
        
        # Layer 2: Deep Pattern Recognition on the 3D topology
        self.lstm = nn.LSTM(3, hidden_size, num_layers, batch_first=True, dropout=0.3)
        
        # Layer 3: Output
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.GELU(),
            nn.Linear(64, 1)
        )
        
    def forward(self, x, orderbook_bids, orderbook_asks, return_physics=False):
        """
        x: (Batch, SeqLen, 4)
        orderbook_bids: (Batch, SeqLen, 5)
        orderbook_asks: (Batch, SeqLen, 5)
        """
        # 1. Calculate Orderbook Gravity
        gravity = self.orderbook_gravity(orderbook_bids, orderbook_asks)
        # Add feature dimension to gravity (Batch, SeqLen) -> (Batch, SeqLen, 1)
        gravity = gravity.unsqueeze(-1)
        
        # 2. Expand the pure 5D DNA into the 34D physical manifold
        manifold = self.physics(x)
        
        # 3. Concatenate Gravity into the Manifold
        manifold = torch.cat([manifold, gravity], dim=-1)
        
        manifold_norm = self.norm(manifold)
        
        # 4. Console9 Compression: Preserving the topology while forcing a 3D bottleneck
        latent_3d = self.latent_compressor(manifold_norm)
        latent_3d = self.console9(latent_3d)
        
        # 5. Temporal LSTM
        lstm_out, _ = self.lstm(latent_3d)
        
        # 6. Predict the final target using the last time step
        pred = self.fc(lstm_out[:, -1, :])
        
        if return_physics:
            return pred, manifold_norm[:, -1, :]
        return pred

if __name__ == "__main__":
    import traceback
    print("Initializing Gen7 Physics-Informed Brain...")
    model7 = Gen7ProphitNet()
    mock_input = torch.randn(2, 60, 4)
    try:
        prediction7 = model7(mock_input)
        print(f"[Gen7] Input Shape: {mock_input.shape}")
        print(f"[Gen7] Prediction Shape: {prediction7.shape} -> SUCCESS")
    except Exception as e:
        print(f"[Gen7] ERROR: {e}")
        
    print("\n" + "="*40 + "\n")
    
    print("Initializing Gen8 (Orderbook Gravity) Brain...")
    try:
        model8 = Gen8ProphitNet()
        # Mock Data: Batch Size=2, Sequence=60 candles, 4 Price Features
        mock_price = torch.randn(2, 60, 4)
        # Mock Orderbook: 5 levels of bids and asks
        mock_bids = torch.rand(2, 60, 5) * 100  # Positive volume
        mock_asks = torch.rand(2, 60, 5) * 100
        
        prediction8 = model8(mock_price, mock_bids, mock_asks)
        print(f"[Gen8] Price Shape: {mock_price.shape}")
        print(f"[Gen8] Bids Shape: {mock_bids.shape}")
        print(f"[Gen8] Asks Shape: {mock_asks.shape}")
        print(f"[Gen8] Prediction Shape: {prediction8.shape} -> SUCCESS")
        print("\n[V8 ENGINE STARTUP] - ALL CYLINDERS FIRING. NO TENSOR ERRORS.")
    except Exception as e:
        print(f"[Gen8] CRASHED ON STARTUP: {e}")
        traceback.print_exc()
    
    # Let's inspect what the model 'learned' before training
    alpha_z33 = torch.sigmoid(model7.physics.z_trinity.ewma_mu.alpha_raw).item()
    implied_span = (2.0 / alpha_z33) - 1.0
    print(f"Initial Z_Trinity Span: {implied_span:.2f}")
