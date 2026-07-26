"""
   / \      / \
  /   \    /   \      T H E _ M E S S E N G E R
 |  !  |--|  ?  |     [SIGNAL_ROUTER]
  \___/    \___/
   | |      | |       [LAYER]:     COMM_LINK
   |_|      |_|       [FREQUENCY]: ASYNC_PUSH
                      [AUTHORITY]: SYSTEM_R00T
                      [PHASE]:     27 (GLITCH_III)
"""

import aiohttp
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("Messenger")

class Messenger:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        # STEALTH: Common Avatar URL (e.g. The Rat)
        self.avatar_url = "https://i.imgur.com/8QZ9X9a.png" 
        self.username = "AURATIC SYSTEMS PRIME"

    async def send_trade_alert(self, trade: Dict[str, Any]):
        """
        Sends a rich embed to Discord.
        """
        if not self.webhook_url:
            return

        try:
            side = trade.get('side', 'UNKNOWN').upper()
            symbol = trade.get('symbol', 'UNKNOWN')
            price = trade.get('price', 0)
            qty = trade.get('qty', 0)
            mode = trade.get('mode', 'PAPER')
            pnl = trade.get('pnl', None)
            
            # Color Logic
            color = 0x00FF00 if side == 'BUY' else 0xFF0000 
            if side == 'SELL' and pnl and pnl > 0: color = 0x00FF00 # Profitable Sell
            
            emoji = "🟢" if side == 'BUY' else "🔴"
            title = f"{emoji} {side} {symbol}"
            
            if mode == 'PAPER':
                title += " [SIMULATION]"
            
            description = f"**Price:** ${price}\n**Size:** {qty}"
            
            if pnl is not None:
                pnl_emoji = "💰" if pnl > 0 else "💸"
                description += f"\n**PnL:** {pnl_emoji} ${pnl:.2f}"

            payload = {
                "username": self.username,
                "avatar_url": self.avatar_url,
                "embeds": [{
                    "title": title,
                    "description": description,
                    "color": color,
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {"text": f"Phase 27 | {mode}"}
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status not in [200, 204]:
                        logger.warning(f"Failed to send Discord alert: {response.status}")

        except Exception as e:
            logger.error(f"Messenger Fault: {e}")

    async def send_message(self, message: str):
        """Send simple text message."""
        if not self.webhook_url: return
        try:
            payload = {"content": message, "username": self.username, "avatar_url": self.avatar_url}
            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json=payload)
        except Exception:
            pass

# Singleton
_messenger = None

def get_messenger() -> Messenger:
    global _messenger
    if _messenger is None:
        _messenger = Messenger()
    return _messenger
