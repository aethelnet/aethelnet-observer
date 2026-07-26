import numpy as np
from scipy.integrate import solve_ivp
import math
import time
import threading
from services.database import get_database
try:
    from scipy.signal import periodogram
    from numba import jit
    HAS_ADVANCED_MATH = True
    print("[PHYSICS] Advanced Math (Numba/Scipy) ENABLED")
except ImportError:
    HAS_ADVANCED_MATH = False
    print("[PHYSICS] WARNING: Advanced Math DISABLED. Running in Fallback Mode.")
    # Dummy jit decorator if numba is missing
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

def calculate_velocity(position, velocity, force, mass, dt=0.01):
    return velocity + (force / mass) * dt

def calculate_force(position, velocity, acceleration, mass, drag_coefficient, spring_constant, damping_ratio, dt=0.01):
    velocity_squared = velocity ** 2
    position_squared = position ** 2
    kinetic_energy = (1 / 2) * mass * velocity_squared
    potential_energy = (1 / 2) * spring_constant * position_squared
    total_energy = kinetic_energy + potential_energy
    work_done = -damping_ratio * total_energy
    force_done = work_done / dt
    return force_done - (drag_coefficient * velocity)

def integrate(position, velocity, acceleration, mass, drag_coefficient, spring_constant, damping_ratio, time_span, time_step):
    t_span = (time_span[0], time_span[1])
    y0 = [position, velocity]
    
    def dynamics(t, y):
        pos, vel = y
        force = calculate_force(pos, vel, acceleration, mass, drag_coefficient, spring_constant, damping_ratio, time_step)
        accel = force / mass
        return [vel, accel]
    
    solver = solve_ivp(dynamics, t_span, y0, t_eval=np.arange(t_span[0], t_span[1], time_step))
    return solver.y

def calc_spectral_entropy(data, fs=1.0):
    """
    Calculates Spectral Entropy.
    H = -sum(p * log2(p))
    
    Normalized to [0,1] by dividing by log2(N), where N is the number of frequency bins.
    Returns 0.0 for constant signals or when total power is zero.
    
    Higher values (closer to 1.0) indicate more randomness/noise.
    Lower values (closer to 0.0) indicate more structure/predictability.
    """
    if len(data) < 10: return 0.0
    
    # Detrend
    data = np.array(data)
    data = data - np.mean(data)
    
    # Check for constant signal
    if np.all(data == 0) or np.std(data) < 1e-10:
        return 0.0
    
    try:
        # Try using scipy's periodogram if available
        if HAS_ADVANCED_MATH:
            # Power Spectral Density
            freqs, psd = periodogram(data, fs=fs)
            
            # Normalize PSD to get probability distribution
            psd_norm = psd / (np.sum(psd) + 1e-9)
            
            # Entropy
            # Filter out 0s to avoid log(0)
            psd_norm = psd_norm[psd_norm > 0]
            if len(psd_norm) == 0: return 0.0
            
            h = -np.sum(psd_norm * np.log2(psd_norm))
            
            # Normalize by log2(N) to get 0..1 range
            h_norm = h / np.log2(len(psd_norm))
            return h_norm
        else:
            # Fallback to numpy FFT
            n = len(data)
            fft_vals = np.fft.fft(data)
            power = np.abs(fft_vals)**2
            
            # Only use positive frequencies (first half + DC)
            half_n = n // 2 + 1
            power = power[:half_n]
            
            # Normalize to get probability distribution
            total_power = np.sum(power)
            if total_power <= 1e-10:
                return 0.0
                
            pdf = power / total_power
            
            # Filter out zeros
            pdf = pdf[pdf > 1e-10]
            if len(pdf) == 0: return 0.0
            
            # Calculate entropy
            entropy = -np.sum(pdf * np.log2(pdf))
            
            # Normalize
            max_entropy = np.log2(len(pdf))
            if max_entropy > 0:
                entropy /= max_entropy
                
            return entropy
    except Exception as e:
        print(f"Spectral entropy calculation error: {e}")
        return 0.5  # Return middle value as fallback

def calc_spectral_entropy_numba(x, fs=1.0):
    """
    Wrapper for spectral entropy calculation.
    Uses the non-numba version for compatibility.
    """
    return calc_spectral_entropy(x, fs)

class PhysicsCore:
    """Core physics engine for market dynamics simulation."""
    
    def __init__(self):
        self.mass = 1.0
        self.drag_coefficient = 0.1
        self.spring_constant = 1.0
        self.damping_ratio = 0.1
        
    def calculate_market_force(self, price_data, volume_data):
        """Calculate market forces based on price and volume."""
        if len(price_data) < 2:
            return 0.0
            
        # Simple momentum calculation
        price_change = price_data[-1] - price_data[-2] if len(price_data) >= 2 else 0.0
        volume_factor = volume_data[-1] if volume_data else 1.0
        
        return price_change * volume_factor * 0.001  # Scale factor
        
    def simulate_dynamics(self, initial_position, initial_velocity, force, time_steps=100):
        """Simulate market dynamics over time."""
        positions = [initial_position]
        velocities = [initial_velocity]
        
        dt = 0.01
        for _ in range(time_steps):
            current_pos = positions[-1]
            current_vel = velocities[-1]
            
            # Calculate acceleration
            acceleration = (force - self.drag_coefficient * current_vel - 
                          self.spring_constant * current_pos) / self.mass
            
            # Update velocity and position
            new_vel = current_vel + acceleration * dt
            new_pos = current_pos + new_vel * dt
            
            velocities.append(new_vel)
            positions.append(new_pos)
            
        return positions, velocities

class HydroFractalEngine:
    """Advanced fractal analysis engine for market patterns."""
    
    def __init__(self):
        self.physics_core = PhysicsCore()
        self.fractal_dimension = 1.5
        self.turbulence_factor = 0.1
        
    def calculate_fractal_dimension(self, price_series):
        """Calculate the fractal dimension of a price series."""
        if len(price_series) < 10:
            return 1.5  # Default value
            
        try:
            # Simple box-counting method approximation
            data = np.array(price_series)
            data = data - np.mean(data)  # Center the data
            
            # Calculate variance at different scales
            scales = [2, 4, 8, 16]
            variances = []
            
            for scale in scales:
                if len(data) >= scale * 2:
                    downsampled = data[::scale]
                    if len(downsampled) > 1:
                        variances.append(np.var(downsampled))
                    else:
                        variances.append(0.0)
                else:
                    variances.append(0.0)
            
            # Estimate fractal dimension from variance scaling
            if len(variances) >= 2 and variances[0] > 0:
                # Simple approximation
                ratio = variances[1] / variances[0] if variances[0] > 0 else 1.0
                fractal_dim = 1.0 + 0.5 * np.log(ratio) / np.log(2.0)
                return max(1.0, min(2.0, fractal_dim))  # Clamp to reasonable range
            
            return 1.5
            
        except Exception as e:
            print(f"Fractal dimension calculation error: {e}")
            return 1.5
            
    def analyze_turbulence(self, price_data, volume_data):
        """Analyze market turbulence using hydro-fractal methods and persist physics state.
        Computes a set of heuristic 'alpha' physics factors:
          - momentum: short-term price change
          - strain: peak short-term absolute change
          - force: market force from PhysicsCore
          - squeeze: short-term vs long-term volatility ratio
          - flow: recent volume flow
          - entropy: spectral entropy (existing)
          - jerk: change of acceleration approximation
          - sympathy: correlation between price and volume (last window)
        Persists these factors to the DB as analysis_type='physics_state' (best-effort).
        """
        if len(price_data) < 20:
            return {"turbulence": 0.0, "fractal_dimension": 1.5, "entropy": 0.0}
            
        try:
            # Calculate fractal dimension
            fractal_dim = self.calculate_fractal_dimension(price_data)
            
            # Calculate spectral entropy
            entropy = calc_spectral_entropy(price_data[-50:])  # Use last 50 points
            
            # Calculate volatility measures
            price_volatility = float(np.std(price_data[-20:])) if len(price_data) >= 20 else 0.0
            volume_volatility = float(np.std(volume_data[-20:])) if len(volume_data) >= 20 else 0.0
            
            # Momentum (short term)
            momentum = float(price_data[-1] - price_data[-5]) if len(price_data) >= 5 else 0.0
            
            # Strain: max absolute short-term diff
            if len(price_data) >= 2:
                recent_seg = price_data[-10:] if len(price_data) >= 10 else price_data
                recent_diffs = np.abs(np.diff(recent_seg))
                strain = float(np.max(recent_diffs)) if recent_diffs.size > 0 else 0.0
            else:
                strain = 0.0
            
            # Force from physics core (reuse existing PhysicsCore)
            try:
                force = float(self.physics_core.calculate_market_force(price_data, volume_data))
            except Exception:
                force = 0.0
            
            # Squeeze: ratio of short-term to long-term vol (avoid div0)
            short_vol = float(np.std(price_data[-10:])) if len(price_data) >= 10 else price_volatility
            long_vol = float(np.std(price_data[-50:])) if len(price_data) >= 50 else max(short_vol, 1e-9)
            squeeze = float(short_vol / (long_vol + 1e-9))
            
            # Flow: recent volume minus recent mean
            if len(volume_data) >= 1:
                recent_vol_mean = float(np.mean(volume_data[-20:])) if len(volume_data) >= 5 else float(np.mean(volume_data))
                flow = float((volume_data[-1]) - recent_vol_mean)
            else:
                flow = 0.0
            
            # Jerk: discrete approximation of third derivative of price
            if len(price_data) >= 4:
                a1 = price_data[-1] - 2 * price_data[-2] + price_data[-3]
                a2 = price_data[-2] - 2 * price_data[-3] + price_data[-4]
                jerk = float(a1 - a2)
            else:
                jerk = 0.0
            
            # Sympathy: correlation between price and volume over window
            sympathy = 0.0
            try:
                window = min(len(price_data), len(volume_data))
                if window >= 5:
                    p = np.array(price_data[-window:])
                    v = np.array(volume_data[-window:])
                    if np.std(p) > 0 and np.std(v) > 0:
                        sympathy = float(np.corrcoef(p, v)[0, 1])
            except Exception:
                sympathy = 0.0
            
            # Calculate turbulence factor (retain previous heuristic)
            turbulence = (price_volatility * volume_volatility * entropy) / (fractal_dim + 0.1)
            
            result = {
                "turbulence": float(turbulence),
                "fractal_dimension": float(fractal_dim),
                "entropy": float(entropy),
                "price_volatility": float(price_volatility),
                "volume_volatility": float(volume_volatility)
            }
            
            # Persist full physics state to DB asynchronously (best-effort)
            payload = {
                "momentum": float(momentum),
                "strain": float(strain),
                "force": float(force),
                "squeeze": float(squeeze),
                "flow": float(flow),
                "entropy": float(entropy),
                "jerk": float(jerk),
                "sympathy": float(sympathy),
                "price_volatility": float(price_volatility),
                "volume_volatility": float(volume_volatility),
                "fractal_dimension": float(fractal_dim),
                "turbulence": float(turbulence),
                "timestamp": time.time()
            }
            
            def _persist():
                try:
                    db = get_database()
                    ts = time.time()
                    if hasattr(db, "insert_analysis"):
                        try:
                            # Preferred signature used elsewhere: insert_analysis(symbol, ts, type, payload)
                            db.insert_analysis("physics", ts, "physics_state", payload)
                        except TypeError:
                            # Try a couple of alternate common signatures (best-effort)
                            try:
                                db.insert_analysis(ts, "physics_state", payload)
                            except Exception:
                                try:
                                    db.insert_analysis("physics_state", payload)
                                except Exception:
                                    pass
                except Exception:
                    # Swallow persistence errors; physics analysis should not crash main loop
                    pass
            
            threading.Thread(target=_persist, daemon=True).start()
            
            return result
            
        except Exception as e:
            print(f"Turbulence analysis error: {e}")
            return {"turbulence": 0.0, "fractal_dimension": 1.5, "entropy": 0.0}
            
    def predict_next_movement(self, price_data, volume_data, steps_ahead=1):
        """Predict next price movement using hydro-fractal analysis."""
        if len(price_data) < 10:
            return {"prediction": 0.0, "confidence": 0.0}
            
        try:
            # Analyze current turbulence
            analysis = self.analyze_turbulence(price_data, volume_data)
            
            # Calculate market force
            force = self.physics_core.calculate_market_force(price_data, volume_data)
            
            # Simple prediction based on momentum and turbulence
            recent_change = price_data[-1] - price_data[-2] if len(price_data) >= 2 else 0.0
            turbulence_factor = analysis["turbulence"]
            
            # Prediction with turbulence dampening
            prediction = recent_change * (1.0 - turbulence_factor * 0.5) + force * 0.1
            
            # Confidence based on fractal dimension (more structured = higher confidence)
            confidence = max(0.0, min(1.0, (2.0 - analysis["fractal_dimension"]) / 1.0))
            
            return {
                "prediction": float(prediction),
                "confidence": float(confidence),
                "analysis": analysis
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {"prediction": 0.0, "confidence": 0.0}
