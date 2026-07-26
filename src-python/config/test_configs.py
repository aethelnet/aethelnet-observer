"""
Test Configurations for Component Impact Analysis

Each config enables/disables specific components to isolate their impact.
These are used by test_component_impact.py to run comparative simulations.
"""

# ============================================================================
# BASELINE: Minimal Momentum-Only Configuration
# Pure z-score momentum following with no modifiers
# ============================================================================
BASELINE_CONFIG = {
    "name": "baseline",
    "description": "Pure momentum (z-score only), no filters, no modifiers",
    
    # Signal Generation
    "USE_NEURAL_SIGNAL": False,  # Disable DMD/Hilbert synthesis
    
    # Signal Modifiers  
    "USE_STRATEGY_ENSEMBLE": False,  # No ensemble voting
    "USE_RAT_MEAN_REVERSION": False, # No mean reversion (signal inversion)
    "USE_RAT_AUTOPILOT": False,      # DEPRECATED (backwards compat)
    "USE_RAT_FILTER": False,
    "USE_RAT_ENHANCE": False,
    "SHADOW_ENGINE_ENABLED": False,  # No shadow validation
    
    # Filters
    "IGNORE_REGIME_FILTER": True,    # No EQUI blocking
    "ORACLE_ENABLED": False,
    "SIGNAL_PERSISTENCE": 1,         # Instant execution
    
    # Risk Management
    "SIGNAL_THRESHOLD": 0.59,
    "MAX_POSITION_SIZE": 0.04,
    "EXECUTION_ENABLED": False,      # Paper trading
}

# ============================================================================
# BASELINE + ENSEMBLE: Add Strategy Voting
# Tests if ensemble improves or dilutes momentum signals
# ============================================================================
ENSEMBLE_CONFIG = {
    "name": "ensemble",
    "description": "Baseline + ensemble voting from multiple strategies",
    **BASELINE_CONFIG,  # Inherit baseline
    
    # Override: Enable ensemble
    "USE_STRATEGY_ENSEMBLE": True,
    "name": "ensemble",  # Re-set name after inheritance
    "description": "Baseline + ensemble voting from multiple strategies",
}

# ============================================================================
# BASELINE + REGIME FILTER: Add EQUI Market Blocking
# Tests if blocking choppy markets improves performance
# ============================================================================
REGIME_FILTER_CONFIG = {
    "name": "regime_filter",
    "description": "Baseline + regime filter (blocks EQUI/chop markets)",
    **BASELINE_CONFIG,
    
    # Override: Enable regime filter
    "IGNORE_REGIME_FILTER": False,
    "name": "regime_filter",
    "description": "Baseline + regime filter (blocks EQUI/chop markets)",
}

# ============================================================================
# BASELINE + RAT: Add Mean Reversion Override
# Tests if Rat's counter-trend logic improves performance
# ============================================================================
RAT_CONFIG = {
    "name": "rat",
    "description": "Baseline + Rat mean-reversion (INVERTS signals for counter-trend)",
    **BASELINE_CONFIG,
    
    # Override: Enable Rat mean-reversion (signal inversion)
    "USE_RAT_MEAN_REVERSION": True,  # ⚠️ INVERTS SIGNALS
    "USE_RAT_AUTOPILOT": True,       # Backwards compat
    "USE_RAT_FILTER": True,
    "USE_RAT_ENHANCE": True,
    "name": "rat",
    "description": "Baseline + Rat mean-reversion (INVERTS signals for counter-trend)",
}

# ============================================================================
# BASELINE + NEURAL SIGNAL: Add DMD/Hilbert/Phase
# Tests if advanced math (Exoskeleton) improves signals
# ============================================================================
NEURAL_CONFIG = {
    "name": "neural",
    "description": "Baseline + neural signal synthesis (DMD/Hilbert/Phase)",
    **BASELINE_CONFIG,
    
    # Override: Enable neural signal
    "USE_NEURAL_SIGNAL": True,
    "name": "neural",
    "description": "Baseline + neural signal synthesis (DMD/Hilbert/Phase)",
}

# ============================================================================
# BASELINE + SHADOW ENGINE: Add Parallel Validation
# Tests if shadow engine's feedback improves position sizing
# ============================================================================
SHADOW_CONFIG = {
    "name": "shadow",
    "description": "Baseline + shadow engine (ghost trade validation)",
    **BASELINE_CONFIG,
    
    # Override: Enable shadow
    "SHADOW_ENGINE_ENABLED": True,
    "name": "shadow",
    "description": "Baseline + shadow engine (ghost trade validation)",
}

# ============================================================================
# ALL FEATURES: Everything Enabled
# Maximum complexity configuration
# ============================================================================
ALL_FEATURES_CONFIG = {
    "name": "all_features",
    "description": "All components enabled (maximum complexity)",
    
    # Signal Generation
    "USE_NEURAL_SIGNAL": True,
    
    # Signal Modifiers
    "USE_STRATEGY_ENSEMBLE": True,
    "USE_RAT_MEAN_REVERSION": True,  # ⚠️ Mean reversion enabled (inverts signals)
    "USE_RAT_AUTOPILOT": True,       # Backwards compat
    "USE_RAT_FILTER": True,
    "USE_RAT_ENHANCE": True,
    "SHADOW_ENGINE_ENABLED": True,
    
    # Filters
    "IGNORE_REGIME_FILTER": False,  # Filter active
    "ORACLE_ENABLED": False,        # Keep disabled (torch issues)
    "SIGNAL_PERSISTENCE": 3,
    
    # Risk Management
    "SIGNAL_THRESHOLD": 0.59,
    "MAX_POSITION_SIZE": 0.04,
    "EXECUTION_ENABLED": False,
}

# ============================================================================
# CURRENT PRODUCTION: Actual Current Settings
# What's running right now in production
# ============================================================================
CURRENT_PRODUCTION_CONFIG = {
    "name": "current_production",
    "description": "Current production settings (as of 2026-01-29)",
    
    # Signal Generation
    "USE_NEURAL_SIGNAL": True,  # Neural signal active
    
    # Signal Modifiers
    "USE_STRATEGY_ENSEMBLE": True,     # Ensemble active
    "USE_RAT_MEAN_REVERSION": False,   # Mean reversion OFF (momentum following)
    "USE_RAT_AUTOPILOT": False,        # DEPRECATED (backwards compat)
    "USE_RAT_FILTER": True,            # Rat filter ON (safety only, doesn't invert)
    "USE_RAT_ENHANCE": True,           # Rat enhance ON (ML boost, doesn't invert)
    "SHADOW_ENGINE_ENABLED": True,     # Shadow active
    
    # Filters
    "IGNORE_REGIME_FILTER": False,   # Regime filter active (blocks EQUI)
    "ORACLE_ENABLED": False,         # Oracle disabled
    "SIGNAL_PERSISTENCE": 3,
    
    # Risk Management
    "SIGNAL_THRESHOLD": 0.59,
    "MAX_POSITION_SIZE": 0.04,
    "HYPERLIQUID_LEVERAGE": 20.0,
    "BINANCE_LEVERAGE": 3.0,
    "EXECUTION_ENABLED": False,
}

# ============================================================================
# TEST SUITE: All configurations in order
# ============================================================================
ALL_TEST_CONFIGS = [
    BASELINE_CONFIG,
    NEURAL_CONFIG,
    SHADOW_CONFIG,
    REGIME_FILTER_CONFIG,
    ENSEMBLE_CONFIG,
    RAT_CONFIG,
    ALL_FEATURES_CONFIG,
    CURRENT_PRODUCTION_CONFIG,
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config(name: str) -> dict:
    """Get a test config by name"""
    for config in ALL_TEST_CONFIGS:
        if config["name"] == name:
            return config
    raise ValueError(f"Unknown config: {name}. Available: {[c['name'] for c in ALL_TEST_CONFIGS]}")

def list_configs() -> list:
    """List all available test configurations"""
    return [(c["name"], c["description"]) for c in ALL_TEST_CONFIGS]

def apply_config(config: dict, settings_obj):
    """
    Apply a test configuration to a settings object.
    
    Args:
        config: Dict of configuration overrides
        settings_obj: Settings object to modify
    
    Returns:
        Modified settings object
    """
    for key, value in config.items():
        if key not in ['name', 'description']:  # Skip metadata
            setattr(settings_obj, key, value)
    return settings_obj

