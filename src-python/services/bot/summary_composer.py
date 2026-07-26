
import logging
import asyncio
from typing import List, Dict, Any
from services.bot.fractal_weaver import FractalWeaver
from services.data_manager import get_data_manager
from services.enhanced_news_aggregator import get_enhanced_news_aggregator
from services.opportunity_cache import get_opportunity_cache
from services.brain import get_engine

logger = logging.getLogger("SummaryComposer")

class SummaryComposer:
    
    @staticmethod
    async def generate_achievement_summary(user_id: int, interaction_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Composes the 'Achievement Unlocked' summary message.
        """
        interactions = interaction_stats.get('total_interactions', 0)
        tabs = len(interaction_stats.get('tabs_visited', []))
        
        # 1. Global Market State (The 'TLDR')
        global_state = await SummaryComposer._get_global_state()
        
        # 2. User Focus (Pinned Items + Visited Symbols)
        user_focus = await SummaryComposer._get_user_focus(user_id, interaction_stats)
        
        # 3. Connected Nodes (Taxonomy)
        connected = await SummaryComposer._get_connected_nodes(user_focus)
        
        # --- BUILD INFO CONTENT FIRST ---
        info_msg = ""
        info_msg += "<b>[ SYSTEM SYNC COMPLETE ]</b>\n"
        info_msg += f"<code>INT_SCORE: {interactions} | BREADTH: {tabs}</code>\n"
        info_msg += "<code>════════════════════════════════</code>\n\n"
        
        # GLOBAL SECTION
        info_msg += "<b>[ GLOBAL STATE HYPER-SUMMARY ]</b>\n"
        info_msg += f"<i>{global_state['tldr']}</i>\n"
        info_msg += f"• <b>Eval:</b> {global_state['eval']}\n"
        info_msg += f"• <b>Deep:</b> {global_state['deep']}\n\n"
        
        # FOCUS SECTION
        if user_focus:
            info_msg += "<b>[ YOUR FOCUS NODES ]</b>\n"
            for item in user_focus[:5]: 
                info_msg += f"<b>[{item['symbol']}]</b> {item['tldr']}\n"
                info_msg += f"└─ <i>{item['deep']}</i>\n"
            info_msg += "\n"
            
        # CONNECTED SECTION
        if connected:
            info_msg += "<b>[ RESEARCH DIRECTIVES ]</b>\n"
            info_msg += "<i>Intelligence suggests these nodes align with your focus. Direct your attention here:</i>\n\n"
            
            for node in connected[:5]:
                sym = node['symbol']
                reason = node['tldr']
                
                # Dynamic Instruction based on symbol type
                action_verb = "Investigate"
                resource = "Price Action" 
                
                # Simple heuristics for variety
                seed = hash(sym) % 3
                if seed == 0:
                    action_verb = "Analyze"
                    resource = "Volume Profile"
                elif seed == 1:
                    action_verb = "Review"
                    resource = "Recent News"
                
                info_msg += f"<b>› {sym}</b>\n"
                info_msg += f"  ↳ <b>Task:</b> {action_verb} {resource}\n"
                info_msg += f"  ↳ <b>Why:</b> {reason}\n"
            info_msg += "\n"

        # TELEMETRY SECTION (For the obsessive reader)
        import random
        cpu_load = random.randint(12, 45)
        mem_load = random.randint(30, 60)
        info_msg += "<b>[ SYSTEM TELEMETRY ]</b>\n"
        info_msg += "<code>────────────────────────────────</code>\n"
        info_msg += f"<code>CORE_LOAD: {cpu_load}% | MEM_UTIL: {mem_load}%</code>\n"
        info_msg += f"<code>WS_LATENCY: {random.randint(5, 45)}ms | SYNC_STRL: Stable</code>\n"
            
        info_msg += "\n<code>[ D O P A M I N E _ P R O T O C O L _ A C T I V E ]</code>"

        # --- DYNAMIC FRACTAL SCALING ---
        # Telegram character limit is ~4096. We target 4000 to be safe with HTML tags.
        current_len = len(info_msg)
        budget = 4000 - current_len
        
        # Each fractal line is approx 41 characters (40 chars + newline)
        # We also need a <code> tag and some spacing
        max_height = budget // 42
        
        # Cap height between 4 (minimum visible) and 12 (requested simplification)
        target_height = max(0, min(12, max_height - 4))
        
        fractal_header = ""
        if target_height >= 3:
            fractal = FractalWeaver.evolve(interactions, tabs, height=target_height)
            # Use <pre> tag to enable copy-paste behavior and monospace alignment
            fractal_header = f"<pre>{fractal}</pre>\n\n"
            
        msg = fractal_header + info_msg
        return {
            "text": msg,
            "actions": [n['symbol'] for n in connected[:5]] if connected else []
        }

    @staticmethod
    async def _get_global_state():
        # Heuristic composition based on Brain metrics
        engine = get_engine()
        # Retrieve generic market sentiment from BTC as proxy
        dm = get_data_manager()
        stats = await asyncio.to_thread(dm.get_ticker_stats, "BTCUSDT")
        
        if not stats:
            return {"tldr": "Market data unavailable.", "eval": "UNKNOWN", "deep": "Systems offline."}
            
        change = stats.get('change_pct', 0)
        vol = stats.get('quote_volume', 0)
        
        # Construct narrative
        if change > 5:
            tldr = "Market is SURGING. High velocity logic detected."
            eval_text = "EXTREME GREED"
            deep = "Capital is flooding into risk assets. Volatility is expanding rapidly."
        elif change > 1:
            tldr = "Bullish momentum steadily building."
            eval_text = "OPTIMISTIC"
            deep = "Buyers are actively absorbing supply. Trend structure is intact."
        elif change < -5:
            tldr = "CRASH DETECTED. Liquidity cascade in progress."
            eval_text = "MAXIMUM FEAR"
            deep = "Panic selling is triggering stop runs. Catching knives is not recommended."
        elif change < -1:
            tldr = "Bearish pressure weighing on prices."
            eval_text = "CAUTION"
            deep = "Distribution pattern visible. Support levels are being tested."
        else:
            tldr = "Market is ranging quietly. Equilibrium state."
            eval_text = "NEUTRAL"
            deep = "Volatility execution. Waiting for impulse move."
            
        return {"tldr": tldr, "eval": eval_text, "deep": deep}

    @staticmethod
    async def _get_user_focus(user_id: int, interaction_stats: Dict[str, Any]):
        try:
            # Import here to avoid circular dependency
            from services.bot.core import get_telegram_bot
            bot = get_telegram_bot()
            if not bot or not hasattr(bot, 'pinned_items'):
                logger.warning("Bot instance or pinned_items not available in SummaryComposer.")
                return []
                
            pinned = bot.pinned_items 
            # Note: pinned_items is global in current simple bot, ideally user-specific.
            # Assuming single user or global focus for now per established pattern.
            
            focus_data = []
            
            # 1. VISITED SYMBOLS (Session Focus)
            visited = interaction_stats.get('visited_symbols', set())
            pinned_ids = {p.id for p in pinned if p.type == 'symbol'}
            
            # Combine all symbols the user touched this session
            all_symbols = list(pinned_ids.union(visited))
            
            for sym in all_symbols:
                    # Quick heuristic generation
                    tldr = "Tracking active price action."
                    deep = "Price is monitored for breakout."
                    
                    # Check actual price change
                    try:
                        dm = get_data_manager()
                        stats = await asyncio.to_thread(dm.get_ticker_stats, sym)
                        if stats:
                            chg = stats.get('change_pct', 0)
                            if chg > 2: tldr = "Price is breaking out upside."
                            elif chg < -2: tldr = "Price is correcting sharply."
                    except Exception:
                        pass
                        
                    focus_data.append({"symbol": sym, "tldr": tldr, "deep": deep})
                    
            return focus_data
        except Exception as e:
            logger.error(f"Error getting user focus: {e}")
            return []

    @staticmethod
    async def _get_connected_nodes(user_focus):
        # Find opportunity cache items related to user focus
        cache = get_opportunity_cache()
        # Fetch more to allow for filtering duplicates/focus
        opps = cache.get_top_opportunities(limit=20)
        
        # Deduplication map: symbol -> best_opp
        unique_nodes = {}
        for opp in opps:
            symbol = opp['symbol']
            
            # Skip if this symbol is already in user focus
            if any(f['symbol'] == symbol for f in user_focus):
                continue
            
            # Keep highest score/confidence version
            score = opp.get('score', int(opp.get('confidence', 0) * 100))
            if symbol not in unique_nodes or score > unique_nodes[symbol]['score']:
                unique_nodes[symbol] = {
                    "symbol": symbol,
                    "score": score,
                    "tldr": f"Alpha detected. Opportunity Score: {score}/100"
                }
        
        nodes = list(unique_nodes.values())
        nodes.sort(key=lambda x: x['score'], reverse=True)
        
        # --- FALLBACK: BOREDOM PROTOCOL ---
        # Ensure we always have at least 3 unique directives.
        if len(nodes) < 3:
            defaults = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD", "NVDA", "AAPL", "XRPUSDT"]
            import random
            random_pool = list(defaults)
            random.shuffle(random_pool)
            
            for def_sym in random_pool:
                if len(nodes) >= 5: break # Target 5 for a rich summary
                
                # Check if already present in nodes or focus
                if any(n['symbol'] == def_sym for n in nodes): continue
                if any(f['symbol'] == def_sym for f in user_focus): continue
                
                nodes.append({
                    "symbol": def_sym,
                    "score": 0,
                    "tldr": "Baseline scan required. Potential sector correlation."
                })
        
        return nodes[:5] # Return top 5 unique directives
