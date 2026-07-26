
from datetime import datetime
from typing import Dict, List, Optional, Any

def get_chart_links(symbol: str, tradingview_aff_id: str = "", binance_aff_id: str = "") -> str:
    if not symbol: return ""
    # Static text links removed in favor of UI Buttons
    return ""

def _get_tradingview_url(symbol: str, aff_id: Optional[str] = None) -> str:
    if not symbol: return ""
    symbol_upper = symbol.upper()
    symbol_map = {
        "BTCUSDT": "BINANCE:BTCUSDT", "ETHUSDT": "BINANCE:ETHUSDT", "SOLUSDT": "BINANCE:SOLUSDT",
        "ADAUSDT": "BINANCE:ADAUSDT", "DOGEUSDT": "BINANCE:DOGEUSDT", "XRPUSDT": "BINANCE:XRPUSDT",
        "XAUUSD": "FX:XAUUSD", "EURUSD": "FX:EURUSD", "GBPUSD": "FX:GBPUSD", "USDJPY": "FX:USDJPY",
        "AAPL": "NASDAQ:AAPL", "MSFT": "NASDAQ:MSFT", "GOOGL": "NASDAQ:GOOGL",
        "AMZN": "NASDAQ:AMZN", "TSLA": "NASDAQ:TSLA", "NVDA": "NASDAQ:NVDA", "META": "NASDAQ:META",
    }
    tv_symbol = symbol_map.get(symbol_upper)
    if not tv_symbol:
        if "USDT" in symbol_upper or "USDC" in symbol_upper: tv_symbol = f"BINANCE:{symbol_upper}"
        elif symbol_upper in ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]: tv_symbol = f"FX:{symbol_upper}"
        elif len(symbol_upper) <= 5 and symbol_upper.isalpha(): tv_symbol = f"NASDAQ:{symbol_upper}"
        else: tv_symbol = f"BINANCE:{symbol_upper}"
    url = f"https://www.tradingview.com/chart?symbol={tv_symbol}&interval=15"
    if aff_id: url += f"&aff_id={aff_id}"
    return url

def format_market_summary(timeframe: str, market_data: List[Dict], metrics: Dict, opportunities: List[Dict], predictions: List[Dict], focus_symbols: List[str]) -> str:
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"<b>[ {timeframe.upper()} MARKET ANALYSIS ]</b>\n[TIME] {now_str}\n\n"
    for sym in focus_symbols:
        entry = next((d for d in market_data if d.get('symbol', '').upper() == sym.upper()), None)
        if entry:
            price = entry.get('price', 0)
            change = entry.get('change_24h', 0)
            signal = entry.get('signal_strength', entry.get('signal', 'NEUTRAL'))
            message += f"<b>{sym}</b>: ${price:,.2f} ({change:+.2f}%) [{signal}]\n"
        else:
            pred_entry = next((p for p in predictions if p.get('symbol', '').upper() == sym.upper()), None)
            if pred_entry:
                price = pred_entry.get('current_price', 'N/A')
                preds = pred_entry.get('predictions', [])
                top_pred = preds[0] if preds else {}
                message += f"<b>{sym}</b>: ${price if price!='N/A' else 'N/A'}"
                if top_pred:
                     message += f" → {top_pred.get('predicted_price', 'N/A')} ({int(top_pred.get('confidence',0)*100)}%)"
                message += "\n"
            else:
                message += f"<b>{sym}</b>: data not available\n"
    message += "\n"
    if metrics:
        message += f"<b>[PERFORMANCE]</b>\n"
        message += f"PNL: ${metrics.get('total_pnl', 0):,.2f} | Trades: {metrics.get('total_trades',0)} | Win: {metrics.get('win_rate',0):.1f}%\n"
        message += f"Drawdown: {metrics.get('drawdown_percentage',0):.2f}% | Open: {metrics.get('open_positions',0)}\n\n"
    if opportunities:
        message += f"<b>[OPPORTUNITIES]</b> Top {min(3,len(opportunities))}\n"
        for opp in opportunities[:3]:
            sym = opp.get('symbol','N/A')
            circ = opp.get('opportunity_type','')
            conf = int(opp.get('confidence',0)*100)
            message += f"{sym}: {circ} ({conf}%)\n"
        message += "\n"
    if predictions:
        message += f"<b>[PREDICTIONS]</b> Active forecasts\n"
        for pd in predictions[:3]:
            s = pd.get('symbol','N/A')
            preds = pd.get('predictions',[])
            if preds:
                best = max(preds, key=lambda x: x.get('confidence',0))
                message += f"{s}: {best.get('time_horizon_minutes',0)}m @ ${best.get('predicted_price',0):,.2f} ({int(best.get('confidence',0)*100)}%)\n"
        message += "\n"
    return message

def format_symbol_details(symbol: str, market_data: Optional[Dict], predictions: Optional[Dict], opportunities: Optional[List[Dict]], chart_links: str, style: str = "CORE", divine_metrics: Optional[Dict] = None, auto_pilot: bool = False) -> str:
    from services.aesthetic_service import ASCIIArt
    
    symbol_upper = symbol.upper()
    
    # 1. GENERATE FRACTAL HEADER
    seed_val = sum(ord(c) for c in symbol_upper)
    fractal = ASCIIArt.generate_burning_ship(
        width=42, height=10, iterations=30,
        zoom=2.5 + (seed_val % 3) * 0.2,
        center_x=-1.75 + (seed_val % 5) * 0.01,
        center_y=-0.04
    )
    
    # 2. EXTRACT DATA
    price = market_data.get('price', 0) if market_data else 0
    change_24h = market_data.get('change_24h', 0) if market_data else 0
    change_str = f"{change_24h:+.2f}%"
    price_str = f"${price:,.2f}" if price > 1 else f"${price:,.4f}"
    
    # 3. SIGNAL ANALYSIS
    strength = market_data.get('signal_strength', 'NEUTRAL') if market_data else 'NEUTRAL'
    signal_val = market_data.get('signal', 0) if market_data else 0
    
    # Determine trade recommendation
    if "EXTREME_BUY" in strength or "STRONG_BUY" in strength:
        recommendation = "[BULL] BUY SIGNAL"
        conf_pct = 80 if "EXTREME" in strength else 65
    elif "BUY" in strength:
        recommendation = "[ ~ ] LEAN BUY"
        conf_pct = 55
    elif "EXTREME_SELL" in strength or "STRONG_SELL" in strength:
        recommendation = "[BEAR] SELL SIGNAL"
        conf_pct = 80 if "EXTREME" in strength else 65
    elif "SELL" in strength:
        recommendation = "[ ~ ] LEAN SELL"
        conf_pct = 55
    else:
        recommendation = "[ = ] HOLD / WAIT"
        conf_pct = 50
    
    # Visual gauge
    icon = "▲" if signal_val > 0 else ("▼" if signal_val < 0 else "◇")
    gauge = "░░░░░░░░"
    if "EXTREME_BUY" in strength: gauge = "░░░░●●●●"
    elif "STRONG_BUY" in strength: gauge = "░░░░░●●●"
    elif "BUY" in strength: gauge = "░░░░░░░●"
    elif "SELL" in strength: gauge = "●░░░░░░░"
    elif "STRONG_SELL" in strength: gauge = "●●●░░░░░"
    elif "EXTREME_SELL" in strength: gauge = "●●●●░░░░"
    
    # 4. INTEL SUMMARY (STYLE-AWARE)
    intel_lines = []
    
    # PREDICTIONS
    if predictions and predictions.get('predictions') and style != "WARREN": # Warren ignores ML noise
        top_pred = max(predictions['predictions'], key=lambda x: x.get('confidence', 0))
        direction = top_pred.get('direction', 'NEUTRAL')
        
        # Safe Label Mapping
        if direction == "UP": dir_label = "Bullish"
        elif direction == "DOWN": dir_label = "Bearish"
        else: dir_label = "Neutral"
        
        conf = int(top_pred.get('confidence', 0) * 100)
        intel_lines.append(f"• <b>ML Bias:</b> {dir_label} ({conf}%)")
    
    # OPPORTUNITIES
    if opportunities:
        opp = opportunities[0]
        intel_lines.append(f"• <b>Setup:</b> {opp.get('opportunity_type', 'Detection')}")

    # DIVINE METRICS (BRAIN)
    if divine_metrics:
        phase = divine_metrics.get('hilbert_phase', 0.0)
        stab = divine_metrics.get('stability', 0.0)
        
        # Interpret Phase (Dynamic Hint)
        import math
        p_pi = phase / math.pi
        if -1.0 <= p_pi < -0.5:   
            p_desc = "Bottoming"
            p_hint = "(Cycle: Accumulation Zone)"
        elif -0.5 <= p_pi < 0.0:  
            p_desc = "Rising"
            p_hint = "(Cycle: Uptrend Expansion)"
        elif 0.0 <= p_pi < 0.5:   
            p_desc = "Peaking"
            p_hint = "(Cycle: Distribution Zone)"
        else:                     
            p_desc = "Falling"
            p_hint = "(Cycle: Downtrend Correction)"
        
        # Interpret Stability (Dynamic Hint)
        if stab > 50: s_hint = "(State: Highly Coherent/Safe)"
        elif stab > 20: s_hint = "(State: Moderate/Normal)"
        else: s_hint = "(State: Fragmented/Volatile)"

        intel_lines.append(f"• <b>Divine Phase:</b> {p_desc} ({phase:.2f})")
        intel_lines.append(f"  <i>{p_hint}</i>")
        intel_lines.append(f"• <b>Stability:</b> {stab:.4f}")
        intel_lines.append(f"  <i>{s_hint}</i>")

    # EXPERT METRICS (STYLE FILTERED)
    if market_data:
        regime = market_data.get('regime', 'UNKNOWN')
        z = market_data.get('z_score', 0)
        
        # Interpret Regime (Dynamic Hint)
        if regime == "JOY": r_hint = "(Trend: Strong Bullish)"
        elif regime == "SAD": r_hint = "(Trend: Strong Bearish)"
        elif regime == "ANGER": r_hint = "(Trend: Violent/Panic)"
        elif regime == "EQUI": r_hint = "(Trend: Ranging/Calm)"
        else: r_hint = "(Trend: Mixed/Uncertain)"

        if style == "QUANT":
            # Quant wants detailed mechanics
            intel_lines.append(f"• <b>Entropy:</b> <code>{z:+.2f}</code> (Regime: {regime})")
        elif style == "WARREN":
             intel_lines.append(f"• <b>Fundamentals:</b> (Fetching...)") 
        else: # CORE
            # Balanced
            intel_lines.append(f"• <b>Regime:</b> {regime} (Entropy: <code>{z:+.2f}</code>)")
            intel_lines.append(f"  <i>{r_hint}</i>")

    # 5. ASSEMBLE MESSAGE
    msg = (
        f"<pre>{fractal}</pre>\n"
        f"<b>{symbol_upper}</b> · <code>{price_str}</code> <code>{change_str}</code>\n"
        "<code>════════════════════════════════</code>\n\n"
        
        f"<b>{recommendation}</b> ({conf_pct}% conf)\n"
        f"<code>{gauge}</code> {icon}\n\n"
        
        f"<b>COUNCIL WEIGHT:</b> <code>{'100%' if auto_pilot else '25%'}</code> ({'Autonomous' if auto_pilot else 'Manual Oversight'})\n"
        f"<b>VOL:</b> <code>${market_data.get('volume', 0)/1e6:.1f}M</code>\n\n"
    )
    
    if intel_lines:
        msg += "<b>INTEL</b>\n"
        msg += "\n".join(intel_lines) + "\n\n"
    
    msg += "<code>════════════════════════════════</code>"
    
    return msg

def format_news(news_items: List[Dict], title: str, limit: int = 3) -> str:
    """Format news items - limited and context-specific."""
    from services.aesthetic_service import ASCIIArt
    
    fractal = ASCIIArt.generate_mandelbrot(width=24, height=4, iterations=15)
    message = f"<pre>{fractal}</pre>\n\n"
    message += f"<b>[ {title.upper()} ]</b>\n"
    message += "<code>══════════════════════════</code>\n\n"
    
    if not news_items:
        message += "<i>No relevant news found.</i>\n"
        return message
    
    # Limit to specified amount (default 3)
    for i, news in enumerate(news_items[:limit], 1):
        item_title = news.get('title', 'No title')
        if len(item_title) > 60:
            item_title = item_title[:57] + "..."
        source = news.get('source', '')[:12]
        
        message += f"<b>{i}.</b> {item_title}\n"
        if source:
            message += f"   <code>[{source}]</code>\n"
    
    if len(news_items) > limit:
        message += f"\n<i>+{len(news_items) - limit} more articles</i>\n"
    
    message += "\n<code>══════════════════════════</code>"
    return message

def format_wallet_summary(wallet_data: Dict) -> str:
    message = f"<b>[ WALLET SUMMARY ]</b>\n"
    message += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if not wallet_data:
        message += "[X] Wallet data not available.\n"
        return message
    
    mode = wallet_data.get('execution_mode', 'PAPER')
    testnet = wallet_data.get('testnet', True)
    
    mode_str = "Live Trading" if mode == "LIVE" else "Paper Trading (Simulated)"
    if testnet and mode == "LIVE":
        mode_str += " [TESTNET]"
    
    connected = wallet_data.get('connected', False)
    if not connected and mode == "LIVE":
        mode_str += " [!] CONNECTION FAILED"
        
    message += f"[MODE] {mode_str}\n\n"

    # --- DEBUG INFO ---
    last_error = wallet_data.get('last_error', {})
    if not isinstance(last_error, dict): last_error = {}
    last_debug = wallet_data.get('last_debug', {})
    if last_error.get('hyperliquid'):
        message += f"<b>[ ! ] BROKER ERROR (Hyperliquid)</b>\n"
        message += f"<i>{last_error['hyperliquid']}</i>\n\n"
    if last_debug.get('hyperliquid_address'):
        addr = last_debug['hyperliquid_address']
        short_addr = f"{addr[:6]}...{addr[-4:]}"
        message += f"[LINK] Address: {short_addr}\n\n"
    
    primary_currency = wallet_data.get('primary_currency', 'USDT')
    balances = wallet_data.get('balances', {})
    providers = wallet_data.get('provider_breakdown', {})
    
    total_equity = wallet_data.get('total_equity', 0.0)
    realized_pnl = wallet_data.get('realized_pnl', 0.0)
    unrealized_pnl = wallet_data.get('unrealized_pnl', 0.0)
    
    # 1. CAPITAL SUMMARY
    symbol = "€" if primary_currency == "EUR" else "$"
    message += f"<b>[ CAPITAL SUMMARY ]</b>\n"
    message += f"[EQUITY] <b>{symbol}{total_equity:,.2f}</b> {primary_currency}\n\n"
    
    # 2. PROVIDER BREAKDOWN (The Omni View)
    if providers:
        message += f"<b>[ PROVIDERS ]</b>\n"
        # We need to estimate value per provider.
        # Since API passed 'assets' but not equity per provider, we do a rough calc here or just list them.
        # Better: Just list names and major assets for now until we move full valuation logic to API.
        for name, data in providers.items():
            # Clean name
            p_name = name.replace("_spot", "").replace("_future", "").title()
            # Find major asset (Cash/Stable)
            assets = data.get('assets', {})
            cash = 0.0
            other_assets = 0
            for c in ["USDT", "USDC", "USD", "EUR"]:
                 val = float(assets.get(c, {}).get('free', 0) or 0) + float(assets.get(c, {}).get('locked', 0) or 0)
                 cash += val
            
            for k, v in assets.items():
                if k not in ["USDT", "USDC", "USD", "EUR"]:
                    # Check if significant
                    amt = float(v.get('free', 0)) + float(v.get('locked', 0))
                    if abs(amt) > 0: other_assets += 1
            
            msg_part = f"› <b>{p_name}</b>: ${cash:,.2f} (Cash)"
            if other_assets > 0:
                msg_part += f" + {other_assets} Assets"
            message += msg_part + "\n"
        message += "\n"

    # 3. AGGREGATE STATS
    pnl_marker = "[+]" if realized_pnl >= 0 else "[-]"
    message += f"<b>[ PERFORMANCE ]</b>\n"
    message += f"{pnl_marker} [REALIZED] ${realized_pnl:,.2f}\n"
    
    u_marker = "[+]" if unrealized_pnl >= 0 else "[-]"
    message += f"{u_marker} [UNREALIZED] ${unrealized_pnl:,.2f}\n\n"
    
    message += f"<b>[STATS]</b>\n"
    message += f"[TRADES] {wallet_data.get('total_trades', 0)}\n"
    message += f"[WIN] {wallet_data.get('win_rate', 0.0):.1f}%\n"
    
    # Filter open positions for display count
    raw_positions = wallet_data.get('open_positions', [])
    active_count = len([p for p in raw_positions if float(p.get('quantity', 0)) > 0.00001])
    
    message += f"[POSITIONS] {active_count} open\n\n"
    
    return message

def format_positions(positions: List[Dict]) -> str:
    message = f"<b>[ POSITIONS ] Active Portfolio Status</b>\n"
    message += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    # Filter out dust/ghost positions (less than ~$0.10 worth usually, or 0 qty)
    # Cast to float to handle string inputs safely
    active_positions = [
        p for p in positions 
        if float(p.get('quantity', 0)) > 0.00001
    ]

    if not active_positions:
        message += "No open positions.\n"
    else:
        message += f"[COUNT] {len(active_positions)} open positions\n\n"
        total_unrealized = 0.0
        for pos in active_positions:
            sym = pos.get('symbol', 'N/A')
            side = pos.get('side', 'UNKNOWN')
            entry = pos.get('entry_price', 0)
            current = pos.get('current_price', 0)
            qty = float(pos.get('quantity', 0))
            pnl = pos.get('unrealized_pnl', 0)
            hold_time = pos.get('hold_time_seconds', 0)
            entry_time = pos.get('entry_time', 'N/A')
            
            total_unrealized += pnl
            hold_hours = int(hold_time // 3600)
            hold_mins = int((hold_time % 3600) // 60)
            pnl_marker = "[+]" if pnl > 0 else "[-]"
            
            message += f"<b>{sym} - {side}</b>\n"
            message += f"[ENTRY] ${entry:,.2f} | [CURRENT] ${current:,.2f}\n"
            message += f"[QTY] {qty:.4f} | {pnl_marker} P&L: ${pnl:,.2f}\n"
            message += f"[HOLD] {hold_hours}h {hold_mins}m\n"
            message += f"[ENTRY TIME] {str(entry_time)[:19]}\n\n"
        message += f"<b>Total Unrealized P&L: ${total_unrealized:,.2f}</b>\n"
    return message

def format_trades(trades: List[Dict], limit: int) -> str:
    message = f"<b>[ TRADE LOG ] Historical Execution</b>\n"
    message += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += f"[LIMIT] Last {limit} trades\n\n"
    if not trades:
        message += "No trades recorded in this window.\n"
    else:
        message += f"[COUNT] {len(trades)} trades shown\n\n"
        total_pnl = 0.0
        for trade in trades:
            sym = trade.get('symbol', 'N/A')
            side = trade.get('side', 'UNKNOWN')
            entry = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            qty = trade.get('quantity', 0)
            pnl = trade.get('pnl', 0)
            hold_time = trade.get('hold_time_seconds', 0)
            timestamp = trade.get('timestamp', 'N/A')
            total_pnl += pnl
            hold_hours = hold_time // 3600
            hold_mins = (hold_time % 3600) // 60
            pnl_marker = "[+]" if pnl > 0 else "[-]"
            message += f"<b>{sym} - {side}</b>\n"
            message += f"[ENTRY] ${entry:,.2f} -> [EXIT] ${exit_price:,.2f}\n"
            message += f"[QTY] {qty:.4f} | {pnl_marker} P&L: ${pnl:,.2f}\n"
            message += f"[HOLD] {hold_hours}h {hold_mins}m\n"
            message += f"[TIME] {timestamp[:19]}\n\n"
        message += f"<b>Total P&L: ${total_pnl:,.2f}</b>\n"
    return message

def format_shadow_status(shadow: Dict) -> str:
    message = f"<b>[SHADOW] Shadow Engine Status</b>\n"
    message += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    if not shadow:
         message += "[X] Shadow engine data not available.\n"
         return message
    
    main_pnl = shadow.get('main_pnl', 0)
    shadow_pnl = shadow.get('shadow_pnl', 0)
    performance_ratio = shadow.get('performance_ratio', 0)
    regime = shadow.get('regime_recommendation', 'UNKNOWN')
    
    main_marker = "[+]" if main_pnl > 0 else "[-]"
    shadow_marker = "[+]" if shadow_pnl > 0 else "[-]"
    message += f"<b>[COMPARISON] Performance</b>\n"
    message += f"[MAIN] {main_marker} ${main_pnl:,.2f}\n"
    message += f"[SHADOW] {shadow_marker} ${shadow_pnl:,.2f}\n"
    message += f"[RATIO] {performance_ratio:.2%}\n\n"
    message += f"<b>[REGIME] Recommendation</b>\n"
    message += f"[STATUS] {regime}\n\n"
    
    shadow_stats = shadow.get('shadow_stats', {})
    if shadow_stats:
        message += f"<b>[SHADOW STATS]</b>\n"
        message += f"[PNL] ${shadow_stats.get('total_pnl', 0):,.2f}\n"
        message += f"[TRADES] {shadow_stats.get('total_trades', 0)}\n"
        message += f"[WIN] {shadow_stats.get('win_rate', 0) * 100:.1f}%\n"
        message += f"[POSITIONS] {shadow_stats.get('open_positions', 0)}\n"
        message += f"[EQUITY] ${shadow_stats.get('current_equity', 0):,.2f}\n"
        message += f"[PEAK] ${shadow_stats.get('peak_equity', 0):,.2f}\n"
        message += f"[DRAWDOWN] {shadow_stats.get('drawdown_percentage', 0):.2f}%\n"
    return message

def format_system_status(status: Dict, metrics: Dict) -> str:
    message = f"<b>[STATUS] System Health Check</b>\n"
    message += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    if status:
        message += f"<b>[SYSTEM]</b>\n"
        message += f"[RUNNING] {'[OK]' if status.get('is_running') else '[X]'}\n"
        message += f"[MODE] {status.get('env_mode', 'UNKNOWN')}\n"
        message += f"[EXECUTION] {'ENABLED' if status.get('execution_enabled') else 'DISABLED'}\n"
        message += f"[WEBSOCKET] {'CONNECTED' if status.get('websocket_connected') else 'DISCONNECTED'}\n"
        message += f"[HEARTBEAT] {status.get('last_heartbeat', 'N/A')[:19]}\n\n"
        
        # [ARMADA] Brain Status
        message += f"<b>[BRAIN CORE]</b>\n"
        auto = status.get('autopilot_active', False)
        stealth = status.get('stealth_active', True)
        
        message += f"[AUTOPILOT] {'ENGAGED' if auto else 'MANUAL'}\n"
        message += f"[STRATEGY] {'SNAKE (Stealth)' if stealth else 'RAT (Aggressive)'}\n"
        if status:
            chaos_pct = int(status.get('global_chaos', 0) * 100)
            rec = status.get('recommended_mode', 'UNKNOWN')
            message += f"[CHAOS] {chaos_pct}% (Max)\n"
            message += f"[ADVICE] USE {rec}\n\n"

    if metrics:
        win_rate = metrics.get('win_rate', 0)
        if win_rate <= 1.0 and win_rate > 0: win_rate *= 100.0
        
        message += f"<b>[PERFORMANCE]</b>\n"
        message += f"[TRADES] {metrics.get('total_trades', 0)}\n"
        message += f"[WIN RATE] {win_rate:.1f}%\n"
        message += f"[POSITIONS] {metrics.get('open_positions', 0)} open\n"
        message += f"[PNL] ${metrics.get('total_pnl', 0):,.2f}\n"
        message += f"[DRAWDOWN] {metrics.get('drawdown_percentage', 0):.2f}%\n"
        
        validation = metrics.get('validation', {})
        if validation:
            message += f"<b>[VALIDATION]</b>\n"
            message += f"[READY] {'[OK]' if validation.get('live_ready') else '[X]'}\n"
            message += f"[TRADES MET] {'[OK]' if validation.get('trades_met') else '[X]'}\n"
            message += f"[WIN RATE MET] {'[OK]' if validation.get('win_rate_met') else '[X]'}\n"
            message += f"[DRAWDOWN MET] {'[OK]' if validation.get('drawdown_met') else '[X]'}\n"
            
    message += f"\n[UPTIME] System operational"
    return message

def format_config(config: Dict) -> str:
    message = f"<b>[CONFIG] Trading Configuration</b>\n"
    message += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    if not config:
        message += "[X] Configuration not available.\n"
        return message
    preset = config.get('preset', 'Custom')
    execution = config.get('execution_enabled', False)
    testnet = config.get('testnet', True)
    message += f"<b>[STRATEGY]</b>\n"
    message += f"[PRESET] {preset}\n"
    message += f"[MODE] {'LIVE' if execution else 'PAPER'}"
    if testnet: message += " (TESTNET)"
    message += "\n\n"
    params = config.get('parameters', {})
    if params:
        message += f"<b>[PARAMETERS]</b>\n"
        message += f"[HOLD] Min: {params.get('min_hold_time', 0)}s\n"
        message += f"[THRESHOLD] Signal: {params.get('signal_threshold', 0)}\n"
        message += f"[PERSISTENCE] {params.get('signal_persistence', 0)}\n"
        message += f"[SIZE] Max Position: {params.get('max_position_size', 0):.2%}\n"
        message += f"[STOP] Stop Loss: {params.get('stop_loss', 0):.2%}\n"
        message += f"[TARGET] Profit Target: {params.get('profit_target', 0):.2%}\n\n"
    return message
