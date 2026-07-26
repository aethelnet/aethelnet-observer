
import math
import logging

# Mock settings
class Settings:
    MAX_POSITION_SIZE = 0.04
    SIGNAL_WEIGHTED_SIZING = True
    PYRAMIDING_ENABLED = False
    MAX_Portfolio_ALLOCATION = 0.40
    HYPERLIQUID_LEVERAGE = 20.0
    SIGNAL_THRESHOLD = 0.65

def test_tanh_scaling():
    from services.position_sizer import PositionSizer
    settings = Settings()
    sizer = PositionSizer(settings)
    
    capital = 1000.0
    price = 100.0
    
    # Test cases: Z-score from 0 to 4.0
    signals = [0.0, 0.3, 0.65, 1.2, 2.0, 3.0, 4.0]
    
    print(f"{'Signal (Z)':<12} | {'Neural Mult':<12} | {'Target USD':<12} | {'Alloc %':<12}")
    print("-" * 55)
    
    for sig in signals:
        res = sizer.calculate(
            symbol="BTCUSDC",
            side="BUY",
            capital=capital,
            price=price,
            signal=sig,
            leverage=20.0
        )
        
        # Calculate neural_mult manually for display if needed or pick from reason
        # reason: [NEURAL-PRIMARY] Size: $... | Conviction: 1.23x (tanh) | ...
        reason = res['reason']
        conv_part = reason.split("Conviction: ")[1].split("x")[0]
        neural_mult = float(conv_part)
        
        target_usd = res['target_value_usd']
        alloc_pct = (target_usd / 20.0) / capital * 100 # Back-calculate margin alloc
        
        print(f"{sig:<12.2f} | {neural_mult:<12.2f} | ${target_usd:<11.2f} | {alloc_pct:<12.2f}%")

if __name__ == "__main__":
    test_tanh_scaling()
