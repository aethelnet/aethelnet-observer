import math

class SovereignWatchtower:
    """
    Sovereign Watchtower: Implements ChronoVerse Capital's 1307 Protocol.
    Calculates the 'Liquidity Decay' (Λ) based on temporal fractals.
    """
    
    def __init__(self, anchor_date="13.10.1307"):
        self.anchor_date = anchor_date
        self.i = self.calculate_chrono_constant(anchor_date)
        
    def calculate_chrono_constant(self, date_str):
        """
        Derives the Chrono-Constant (i) dynamically from an anchor date.
        Formula: (Day / 100) + ((Year % 100) / 10000)
        """
        try:
            day, month, year = map(int, date_str.split('.'))
            i = (day / 100.0) + ((year % 100) / 10000.0)
            return i
        except:
            return 0.1307 # Fallback

    def calculate_liquidity_decay(self, pressure, volatility, stability):
        """
        The 1307 Protocol Formula for Permissionless Liquidity Decay:
        Λ = (Pressure * ln(Volatility)) / (Stability * e^(1-i))
        """
        # Ensure values are safe for ln()
        safe_vol = max(1.0001, volatility)
        
        # Λ calculation
        numerator = pressure * math.log(safe_vol)
        denominator = stability * math.exp(1 - self.i)
        
        return numerator / (denominator + 1e-9)

    def calculate_volatility_gearing(self, vix, shadow_liq, credit_spread):
        """
        [Dossier #111] Volatility Gearing (Vg):
        Measures acceleration of IV relative to shadow liquidity contraction.
        Vg = (dVIX / dL_shadow) * ln(C_spread)
        Threshold > 2.85: Immediate 'Flash-Freeze' certainty.
        """
        # ln(C_spread) where C_spread is the credit spread magnitude
        safe_spread = max(1.0001, credit_spread)
        
        # dVIX / dL_shadow proxy
        # Since we don't have derivatives here, we use a ratio of current states
        gearing = (vix / (shadow_liq + 1e-9)) * math.log(safe_spread)
        return gearing

    def calculate_insolvency_coefficient(self, social_panic, deposits, assets, htm_loss):
        """
        [Dossier #111] Insolvency Coefficient (Ic):
        Ic = (D_vol * sigma_social) / (A_liq - nabla_HTM)
        Tracks bank-run velocity vs real-world liquidity.
        """
        numerator = deposits * social_panic
        denominator = (assets - htm_loss) + 1e-9
        return numerator / denominator

    def get_risk_score(self, market_vol, debt_ratio=1.22, trust_index=0.85, vix=20, shadow_liq=1.0, credit_spread=1.1):
        """
        Returns an integrated risk score [0.0 - 1.0].
        Fuses 1307 Protocol with Volatility Gearing.
        """
        # 1. 1307 Liquidity Decay
        vol_magnitude = market_vol * 100.0
        decay = self.calculate_liquidity_decay(debt_ratio, vol_magnitude, trust_index)
        
        # 2. Volatility Gearing
        vg = self.calculate_volatility_gearing(vix, shadow_liq, credit_spread)
        
        # Fusion: Decay is base risk, Vg is the accelerator
        # Normalized: 2.85 is the 'Dead Delta' for Vg
        integrated_score = (decay / 1.5) * 0.6 + (vg / 2.85) * 0.4
        
        return min(1.0, max(0.0, integrated_score))
