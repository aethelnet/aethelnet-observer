from ..base_trader import BaseTrader
from ...services.brain import ProphitEngine
import numpy as np
import random

class GuardianTrader(BaseTrader):
    """
    The Hero.
    Starts weak (Unawakened), learns the hard way.
    Eventually unlocks ProphitEngine (Awakened).
    """
    def __init__(self, name, config=None, awakened=False, episode_id=None):
        super().__init__(name, 50000.0)
        self.config = config if config else {}
        self.awakened = awakened
        self.episode_id = episode_id
        self.engine = ProphitEngine()
        
        # Brain Memory
        self.last_prices = {} # ticker -> price
        self.history_buffer = {} # ticker -> list of prices (for TE)

    def decide(self, galaxy_state):
        print(f"DECIDE: {self.name} Buffer: {list(self.history_buffer.keys())}")
        orders = []
        
        # 1. Ingest Data for CORE (Primary Focus)
        core_state = galaxy_state.get('CORE')
        if not core_state: return []
        
        raw_price = core_state['price']
        time = core_state['time']
        volume = 100.0
        if core_state['history']['volume']:
            volume = core_state['history']['volume'][-1]
            
        # --- RESOURCE-BASED FILTERING (PCA) ---
        # The engine now handles PCA filtering internally in ingest_candle
        self.engine.ingest_candle(time, raw_price, volume)
        
        # Update last prices & history for all tickers
        for t, s in galaxy_state.items():
            print(f"  Processing {t} type: {type(t)}")
            self.last_prices[t] = s['price']
            if t not in self.history_buffer: self.history_buffer[t] = []
            self.history_buffer[t].append(s['price'])
            # Keep buffer small but enough for correlation
            if len(self.history_buffer[t]) > 100:
                self.history_buffer[t].pop(0)
            
        if not self.awakened:
            # --- THE HARD WAY ---
            if self.last_prices.get('CORE_LAST'):
                core_ret = (raw_price - self.last_prices['CORE_LAST']) / self.last_prices['CORE_LAST']
                if core_ret < -0.01:
                    orders.append({'side': 'buy', 'size': 5.0, 'ticker': 'GOLD'})
            self.last_prices['CORE_LAST'] = raw_price
            return orders
            
        else:
            # --- AWAKENED GALAXY BRAIN ---
            
            # 1. Topology Analysis (Who is the Leader?)
            tickers = list(galaxy_state.keys())
            if len(self.history_buffer.get('CORE', [])) > 50:
                # Compute Correlation Matrix
                data = []
                valid_tickers = []
                for t in tickers:
                    if len(self.history_buffer.get(t, [])) == len(self.history_buffer['CORE']):
                        data.append(self.history_buffer[t])
                        valid_tickers.append(t)
                
                if len(data) > 1 and len(data[0]) > 1:
                    try:
                        corr_matrix = np.corrcoef(data)
                        centrality = self.engine.topology.update(corr_matrix, valid_tickers)
                    except Exception as e:
                         print(f"DEBUG: Correlation failed details: {e}")
                         centrality = {}
                else:
                    print(f"DEBUG: Not enough data for correlation. Tickers: {len(tickers)}, Data: {len(data)}")
                    for t in tickers:
                        print(f"  {t}: {len(self.history_buffer.get(t, []))} vs CORE: {len(self.history_buffer.get('CORE', []))}")
                    
                # Find Leader
                centrality_map = centrality.get('centrality', {})
                if not centrality_map:
                     leader = tickers[0]
                else:
                    leader = max(centrality_map, key=centrality_map.get)
                    
                    # 2. Predict based on Leader
                    # If Leader moves, we bet on the Followers (High Correlation)
                    
                    # Get Leader's recent move
                    leader_hist = self.history_buffer[leader]
                    leader_move = (leader_hist[-1] - leader_hist[-2]) / leader_hist[-2] if len(leader_hist) > 1 else 0
                    
                    threshold = self.config.get('action_threshold', 0.005)
                    
                    # 3. Hilbert Phase Timing (Resource-Based)
                    # We want to time entries with the cycle
                    projection = self.engine.compute_projection(lookahead=5)
                    phase = projection.get('phase', 0.0)
                    regime = projection.get('regime', 0)
                    
                    # --- TELEMETRY ---
                    from ...services.telemetry import telemetry
                    
                    # topology_data contains {'centrality': ..., 'edges': ...}
                    topology_data = centrality 
                    
                    brain_state = {
                        'phase': phase,
                        'regime': int(regime),
                        'leader': leader,
                        'centrality': topology_data.get('centrality', {}),
                        'edges': topology_data.get('edges', []),
                        'pnl': self.pnl_history[-1] if self.pnl_history else 0
                    }
                    if hasattr(self, 'episode_id'):
                        print(f"HERO LOGGING: {self.episode_id}")
                        telemetry.log(self.episode_id, len(self.pnl_history), brain_state)
                    else:
                        print("HERO: No episode_id")
                    
                    # Phase Logic: -pi is bottom, +pi is top
                    # If we want to BUY, we prefer Phase < 0 (Rising from bottom)
                    # If we want to SELL, we prefer Phase > 0 (Falling from top)
                    
                    timing_bonus = 1.0
                    if leader_move > 0 and phase < 0: timing_bonus = 1.5 # Buying at bottom
                    if leader_move < 0 and phase > 0: timing_bonus = 1.5 # Selling at top
                    
                    if abs(leader_move) > threshold:
                        side = 'buy' if leader_move > 0 else 'sell'
                        
                        # Execute on Leader
                        orders.append({'side': side, 'size': 10.0 * timing_bonus, 'ticker': leader})
                        
                        # Execute on highly correlated followers
                        leader_idx = valid_tickers.index(leader)
                        for i, t in enumerate(valid_tickers):
                            if t == leader: continue
                            
                            correlation = corr_matrix[leader_idx, i]
                            if correlation > 0.7: # Strong follower
                                orders.append({'side': side, 'size': 10.0 * timing_bonus, 'ticker': t})
                            elif correlation < -0.7: # Strong inverse
                                inv_side = 'sell' if side == 'buy' else 'buy'
                                orders.append({'side': inv_side, 'size': 10.0 * timing_bonus, 'ticker': t})

            return orders

    def mutate(self):
        """
        Evolve parameters slightly.
        """
        # Mutate decay
        self.config['decay'] *= random.uniform(0.9, 1.1)
        self.config['decay'] = max(0.1, min(0.99, self.config['decay']))
        
        # Mutate drag
        self.config['base_drag'] *= random.uniform(0.9, 1.1)
        self.config['base_drag'] = max(0.01, min(1.0, self.config['base_drag']))
        
        # Mutate spring
        self.config['base_spring'] *= random.uniform(0.9, 1.1)
        self.config['base_spring'] = max(0.0001, min(0.1, self.config['base_spring']))
        
        # Mutate Threshold (Laziness)
        if 'action_threshold' not in self.config: self.config['action_threshold'] = 0.005
        self.config['action_threshold'] *= random.uniform(0.9, 1.1)
        self.config['action_threshold'] = max(0.001, min(0.05, self.config['action_threshold']))
        
        return self.config
