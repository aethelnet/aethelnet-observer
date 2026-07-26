
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger("Analysis.Technical")

class TechnicalAnalysis:
    def extract_key_events(self, projection: Dict[str, Any], current_price: float, fair_value: float) -> List[Dict[str, Any]]:
        """
        Extract key market events (lows, highs, reversals, significant moves) from price projection.
        """
        if not projection or 'predicted_prices' not in projection:
            return []
            
        prices = projection['predicted_prices']
        confidences = projection.get('confidences', [])
        times = projection.get('timestamps', [])
        
        events = []
        
        # 1. Local Extrema
        if len(prices) >= 3:
            for i in range(1, len(prices) - 1):
                timestamp_ms = times[i]
                event_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                price = prices[i]
                confidence = confidences[i] if i < len(confidences) else 0.5
                time_str = event_time.strftime('%H:%M')
                
                # Deviation from fair value
                deviation = ((price - fair_value) / fair_value) * 100 if fair_value > 0 else 0
                
                # Local Min
                if prices[i-1] > prices[i] and prices[i] < prices[i+1]:
                    if confidence > 0.4:
                        events.append({
                            'time': event_time, 'time_str': time_str, 'price': price,
                            'type': 'low', 'confidence': confidence,
                            'deviation_pct': deviation,
                            'description': f"Local Low at {time_str}"
                        })
                # Local Max
                elif prices[i-1] < prices[i] and prices[i] > prices[i+1]:
                    if confidence > 0.4:
                        events.append({
                            'time': event_time, 'time_str': time_str, 'price': price,
                            'type': 'high', 'confidence': confidence,
                            'deviation_pct': deviation,
                            'description': f"Local High at {time_str}"
                        })

        # 2. Reversals & Trends (Simplified for modularity)
        if len(prices) >= 3:
             # Basic trend check
             start = prices[0]
             end = prices[-1]
             move = ((end - start)/start)*100 if start > 0 else 0
             if abs(move) > 1.0:
                 t_ms = times[-1]
                 t_dt = datetime.fromtimestamp(t_ms/1000, tz=timezone.utc)
                 events.append({
                     'time': t_dt, 'time_str': t_dt.strftime('%H:%M'), 'price': end,
                     'type': 'projected_end', 'confidence': confidences[-1] if confidences else 0.5,
                     'move_pct': abs(move),
                     'deviation_pct': ((end - fair_value)/fair_value)*100 if fair_value else 0,
                     'description': f"Projected move {move:.2f}%"
                 })
                 
        # Sort and dedupe
        events.sort(key=lambda x: (x.get('confidence', 0), abs(x.get('deviation_pct', 0))), reverse=True)
        return events[:3]

    def get_fair_value(self, prices: List[float], current_price: float) -> Dict[str, Any]:
        if not prices or len(prices) < 10:
            return {'fair_value': current_price, 'deviation_pct': 0.0, 'status': 'neutral'}
        
        fair_value = sum(prices[-20:]) / min(20, len(prices))
        deviation = ((current_price - fair_value) / fair_value) * 100 if fair_value > 0 else 0
        
        status = 'fair'
        if deviation < -2.0: status = 'undervalued'
        elif deviation > 2.0: status = 'overvalued'
        
        return {'fair_value': fair_value, 'deviation_pct': deviation, 'status': status}
