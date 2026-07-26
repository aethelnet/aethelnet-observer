from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import deque
from core.physics import StreamingStats, ButterflySensor


@dataclass
class SymbolState:
    """
    Unified State Container for a single trading symbol.
    Provides type safety and clarity for the BrainEngine analysis loop.
    """
    # Raw History
    price_history: List[float] = field(default_factory=list)
    volume_history: List[float] = field(default_factory=list)
    timestamp_history: List[int] = field(default_factory=list)
    z_score_history: List[float] = field(default_factory=list)
    
    # Statistical Engines
    inc_stats: StreamingStats = field(default_factory=lambda: StreamingStats(window_size=240))
    # exoskeleton removed
    butterfly: ButterflySensor = field(default_factory=ButterflySensor)
    
    # Regime & Signal State
    regime_buffer: deque = field(default_factory=lambda: deque(maxlen=15))
    regime: str = "UNKNOWN"
    neural_signal: float = 0.0
    smoothed_neural_signal: float = 0.0
    ml_probability: float = 0.5
    physics_confidence: float = 0.5
    stability: float = 0.5
    
    # Fractal Swarm (Angelic Horizons)
    z_initiation_11: float = 0.0
    z_trinity_33: float = 0.0
    z_fallen_13: float = 0.0
    z_foundation_111: float = 0.0
    z_illumination_333: float = 0.0
    z_beast_666: float = 0.0
    
    # Metadata & Ext. Intelligence
    divine_metrics: Dict[str, Any] = field(default_factory=dict)
    signal_components: Dict[str, Any] = field(default_factory=dict)
    sentiment_bias: float = 0.0
    ocean_wisdom: Dict[str, Any] = field(default_factory=dict)
    specialist_delta: float = 0.0
    ocean_wisdom_score: float = 0.0
    
    # History Deques (Fibonacci/Temporal)
    vector_history: deque = field(default_factory=lambda: deque(maxlen=40))
    ml_prob_history: deque = field(default_factory=lambda: deque(maxlen=40))
    soul_history: deque = field(default_factory=lambda: deque(maxlen=40))
    heavy_history: deque = field(default_factory=lambda: deque(maxlen=40))
    rhyme_history: deque = field(default_factory=lambda: deque(maxlen=40))
    hindsight_history: deque = field(default_factory=lambda: deque(maxlen=40))
    pending_episodes: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Lifecycle
    last_candle_timestamp: int = 0
    last_brain_update: float = 0.0
    is_hydrating: bool = False
    hydrated: bool = False
