
from datetime import datetime

class MarketReporter:
    def format_market_update(self, timeframe: str, data: dict) -> str:
        """
        Format the massive HTML market update message.
        Expected data keys:
        - market_data (list)
        - metrics (dict)
        - opportunities (list)
        - predictions (list)
        - news (list)
        - system (uptime, etc)
        """
        # Unpack data
        market_data = data.get('market_data', [])
        metrics = data.get('metrics', {})
        actionable = data.get('actionable_trades', [])
        predictions = data.get('key_predictions', [])
        news = data.get('news', [])
        uptime = data.get('uptime', {'h':0, 'm':0})
        
        # Stats
        total_symbols = len(market_data)
        green = sum(1 for m in market_data if m.get('change_24h', 0) > 0)
        red = total_symbols - green
        
        # Message Build
        msg = f"<b>[MARKET] Market Update ({timeframe.upper()})</b>\n"
        msg += f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # TLDR
        msg += f"<b>[TLDR]</b>\n"
        if actionable:
            best = actionable[0]
            msg += f"[SETUP] {best['symbol']} {best['action']} @ ${best['entry_price']:.2f}\n"
            msg += f"   Target: ${best['target_price']:.2f} | Stop: ${best['stop_loss']:.2f}\n"
        else:
            msg += f"[MARKET] {green}↑ {red}↓ | {total_symbols} symbols\n"
            if metrics:
                pnl = metrics.get('total_pnl', 0)
                msg += f"[{'+' if pnl>0 else '-'}] PnL: ${pnl:,.2f} | Win: {metrics.get('win_rate',0):.1f}%\n"
        msg += "\n"
        
        # Setups
        if actionable:
            msg += f"<b>[SETUPS] Top Actions</b>\n"
            for t in actionable[:3]:
                msg += f"{t['symbol']} {t['action']} (${t['entry_price']:.2f}) -> ${t['target_price']:.2f}\n"
            msg += "\n"
        
        # Events
        if predictions:
            msg += f"<b>[EVENTS] Key Events</b>\n"
            for p in predictions[:5]:
                sym = p['symbol']
                evt = p['event']
                msg += f"{sym}: {evt['type']} at {evt['time_str']} (Conf: {int(evt.get('confidence',0)*100)}%)\n"
            msg += "\n"
            
        # Overview
        msg += f"<b>[OVERVIEW]</b>\n"
        msg += f"Up: {green} | Down: {red}\n\n"
        
        # News
        if news:
            msg += f"<b>[NEWS]</b>\n"
            for n in news[:3]:
                msg += f"- {n.get('title','')} ({n.get('symbols',[''])[0]})\n"
        
        msg += f"\n[UPTIME] {uptime.get('h')}h {uptime.get('m')}m"
        return msg

    def format_symbol_update(self, symbol: str, timeframe: str, data: dict) -> str:
        # Simplified symbol update
        d = data.get('symbol_data', {})
        price = d.get('price', 0)
        change = d.get('change_24h', 0)
        signal = d.get('signal_strength', 'NEUTRAL')
        
        msg = f"📈 <b>{symbol.upper()} Update ({timeframe})</b>\n\n"
        msg += f"💰 Price: ${price:,.2f}\n"
        msg += f"📊 Change: {change:+.2f}%\n"
        msg += f"🎯 Signal: {signal}\n"
        
        return msg
