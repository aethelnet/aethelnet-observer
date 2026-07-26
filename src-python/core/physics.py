import math
import threading
import random
import time
import numpy as np
from collections import deque
from typing import Optional, List, Dict, Union
from scipy.integrate import solve_ivp

try:
    from scipy.signal import periodogram
    from numba import jit
    HAS_ADVANCED_MATH = True
except ImportError:
    HAS_ADVANCED_MATH = False
    def jit(*args, **kwargs):
        return lambda func: func

# --- CORE PHYSICS UTILS ---

def ulaw_encode(x: float, u: float = 255.0) -> float:
    if x == 0: return 0.0
    sign = 1.0 if x >= 0 else -1.0
    abs_x = abs(x)
    try:
        val = math.log(1.0 + u * abs_x) / math.log(1.0 + u)
        return sign * val
    except: return x

def tpdf_dither() -> float:
    return (random.random() - random.random()) * 0.0001

def console_encode(x: float) -> float:
    try: return math.sin(max(-1.5, min(1.5, x)) * (math.pi / 2.0))
    except: return 0.0

def console_decode(x: float) -> float:
    try:
        clamped = max(-1.0, min(1.0, x))
        return math.asin(clamped) / (math.pi / 2.0)
    except: return x

def bitshift_gain(value: Union[float, np.ndarray], steps: int) -> Union[float, np.ndarray]:
    return value * (2.0 ** steps)

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

def calculate_ulf_waves(bt, bz):
    if not hasattr(calculate_ulf_waves, "_last_mag"):
        calculate_ulf_waves._last_mag = (bt, bz)
        calculate_ulf_waves._last_intensity = 0.0
        return 0.0
    prev_bt, prev_bz = calculate_ulf_waves._last_mag
    if bt == prev_bt and bz == prev_bz:
        calculate_ulf_waves._last_intensity *= 0.98
        return calculate_ulf_waves._last_intensity
    jerk = math.sqrt((bt - prev_bt)**2 + (bz - prev_bz)**2)
    calculate_ulf_waves._last_mag = (bt, bz)
    new_intensity = min(1.0, jerk / 5.0)
    calculate_ulf_waves._last_intensity = (calculate_ulf_waves._last_intensity * 0.5) + (new_intensity * 0.5)
    return calculate_ulf_waves._last_intensity

def detect_ionospheric_bulge(xray, bz):
    if xray > 1e-5 and bz < -2.0: return 1.0
    return 0.0

def calc_spectral_entropy(data, fs=1.0):
    if len(data) < 10: return 0.0
    data = np.array(data)
    data = data - np.mean(data)
    if np.all(data == 0) or np.std(data) < 1e-10: return 0.0
    try:
        if HAS_ADVANCED_MATH:
            freqs, psd = periodogram(data, fs=fs)
            psd_norm = psd / (np.sum(psd) + 1e-9)
            psd_norm = psd_norm[psd_norm > 0]
            if len(psd_norm) == 0: return 0.0
            h = -np.sum(psd_norm * np.log2(psd_norm))
            return h / np.log2(len(psd_norm))
        else:
            n = len(data)
            fft_vals = np.fft.fft(data)
            power = np.abs(fft_vals)**2
            power = power[:n // 2 + 1]
            total_power = np.sum(power)
            if total_power <= 1e-10: return 0.0
            pdf = power / total_power
            pdf = pdf[pdf > 1e-10]
            if len(pdf) == 0: return 0.0
            entropy = -np.sum(pdf * np.log2(pdf))
            max_entropy = np.log2(len(pdf))
            return entropy / max_entropy if max_entropy > 0 else 0.0
    except Exception: return 0.5

# --- STREAMING & SENSORS ---

class StreamingStats:
    def __init__(self, window_size: int = 60):
        self.window_size = float(window_size)
        self.alpha = 2.0 / (self.window_size + 1.0)
        self.mean = 0.0
        self.variance = 0.0
        self.count = 0
        self.prices = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._last_price = None
        self._dup_count = 0

    def add_price(self, price: float):
        price = float(price)
        with self._lock:
            self.prices.append(price)
            if price == self._last_price:
                self._dup_count += 1
                if self._dup_count > 10: return
            else: self._dup_count = 0
            self._last_price = price
            if self.count == 0:
                self.mean = price
                self.variance = 0.0
            else:
                diff = price - self.mean
                incr = self.alpha * diff
                self.mean += incr
                self.variance = (1.0 - self.alpha) * (self.variance + self.alpha * diff**2)
            self.count += 1

    def get_mean(self) -> float:
        with self._lock: return self.mean

    def get_std(self) -> float:
        with self._lock: return math.sqrt(self.variance) if self.variance > 0 else 0.0

class ButterflySensor:
    def __init__(self, window=20):
        self.window = window
        self.history = []

    def update(self, price):
        self.history.append(float(price))
        if len(self.history) > self.window * 2: self.history.pop(0)
    
    def get_chaos_level(self) -> float:
        if len(self.history) < self.window: return 0.0
        try:
            mid = len(self.history) // 2
            dists = []
            for i in range(mid - 1):
                p1, p2 = self.history[i], self.history[i+1]
                s1, s2 = self.history[mid + i], self.history[mid + i + 1]
                div_i = abs(p1 - s1)
                div_f = abs(p2 - s2)
                if div_i > 0.0001:
                    expansion = math.log((div_f + 1e-8) / (div_i + 1e-8))
                    dists.append(expansion)
            if not dists: return 0.0
            avg_lambda = sum(dists) / len(dists)
            return math.tanh(max(0, avg_lambda) * 1.0)
        except: return 0.0

# --- ENGINES ---

class PhysicsCore:
    def __init__(self):
        self.mass = 1.0
        self.drag_coefficient = 0.1
        self.spring_constant = 1.0
        self.damping_ratio = 0.1
        
    def calculate_market_force(self, price_data, volume_data):
        if len(price_data) < 2: return 0.0
        price_change = price_data[-1] - price_data[-2]
        volume_factor = volume_data[-1] if volume_data else 1.0
        return price_change * volume_factor * 0.001
        
    def simulate_dynamics(self, initial_position, initial_velocity, force, time_steps=100):
        positions, velocities = [initial_position], [initial_velocity]
        dt = 0.01
        for _ in range(time_steps):
            cur_pos, cur_vel = positions[-1], velocities[-1]
            accel = (force - self.drag_coefficient * cur_vel - self.spring_constant * cur_pos) / self.mass
            new_vel = cur_vel + accel * dt
            new_pos = cur_pos + new_vel * dt
            velocities.append(new_vel)
            positions.append(new_pos)
        return positions, velocities

class HydroFractalEngine:
    def __init__(self):
        self.physics_core = PhysicsCore()
        
    def calculate_fractal_dimension(self, price_series):
        if len(price_series) < 10: return 1.5
        try:
            data = np.array(price_series)
            data = data - np.mean(data)
            scales, variances = [2, 4, 8, 16], []
            for scale in scales:
                if len(data) >= scale * 2:
                    ds = data[::scale]
                    if len(ds) > 1: variances.append(np.var(ds))
                    else: variances.append(0.0)
                else: variances.append(0.0)
            if len(variances) >= 2 and variances[0] > 0:
                ratio = variances[1] / variances[0]
                fractal_dim = 1.0 + 0.5 * np.log(ratio) / np.log(2.0)
                return max(1.0, min(2.0, fractal_dim))
            return 1.5
        except Exception: return 1.5
            
    def analyze_turbulence(self, price_data, volume_data):
        if len(price_data) < 20: return {"turbulence": 0.0, "fractal_dimension": 1.5, "entropy": 0.0}
        try:
            fractal_dim = self.calculate_fractal_dimension(price_data)
            entropy = calc_spectral_entropy(price_data[-50:])
            p_vol = float(np.std(price_data[-20:]))
            v_vol = float(np.std(volume_data[-20:])) if volume_data else 0.0
            turbulence = (p_vol * v_vol * entropy) / (fractal_dim + 0.1)
            return {
                "turbulence": float(turbulence),
                "fractal_dimension": float(fractal_dim),
                "entropy": float(entropy),
                "price_volatility": p_vol,
                "volume_volatility": v_vol
            }
        except Exception: return {"turbulence": 0.0, "fractal_dimension": 1.5, "entropy": 0.0}
