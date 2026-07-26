import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger("BeaconHandler")

class BeaconHandler:
    def __init__(self, bot):
        self.bot = bot

    async def handle_beacon(self, chat_id: int):
        """
        Displays the status of the DeAI Passive Income Beacon.
        Shows Pulse, total broadcasts, and individual plug health.
        """
        try:
            from services.beacon_service import get_beacon
            from config import get_settings
            
            beacon = get_beacon()
            settings = get_settings()
            status = beacon.get_status()
            
            is_running = status.get("running", False)
            plugs = status.get("plugs", {})
            total_broadcasts = status.get("total_broadcasts", 0)
            
            # --- HEADER ---
            icon = "🟢" if is_running else "🔴"
            mode = "DRY RUN (LOGS ONLY)" if settings.DEAI_LOG_ONLY else "WET RUN (LIVE STAKING)"
            
            lines = [
                f"<b>{icon} ORACLE BEACON</b>",
                f"Mode: <code>{mode}</code>",
                f"Status: <b>{'ONLINE' if is_running else 'OFFLINE'}</b>",
                f"Pulse Count: <b>{total_broadcasts}</b>",
                "",
                "<b>📡 UPLINKS:</b>"
            ]
            
            # --- PLUGS ---
            if not plugs:
                lines.append("<i>No active uplinks configured.</i>")
            else:
                for name, data in plugs.items():
                    p_icon = "✅" if data.get("success", False) else "⚠️"
                    count = data.get("count", 0)
                    last_err = data.get("last_error")
                    
                    lines.append(f"{p_icon} <b>{name}</b>")
                    lines.append(f"   ├ Signals Sent: {count}")
                    if last_err:
                        lines.append(f"   └ Error: {last_err}")
                    else:
                        lines.append(f"   └ Status: Stable")
            
            lines.append("")
            
            # --- READINESS CHECK ---
            # Simple heuristic for the user
            ready_check = "❌"
            if total_broadcasts > 50 and all(p.get("success") for p in plugs.values()):
                ready_check = "✅"
                
            lines.append("<b>🛡️ WET RUN READINESS:</b>")
            lines.append(f"[{ready_check}] Stability Check (>50 signals)")
            if settings.DEAI_LOG_ONLY:
                 lines.append(f"<i>To go live, set DEAI_LOG_ONLY=False in keys.</i>")
            
            msg = "\n".join(lines)
            await self.bot.send_message(chat_id, msg)
            
        except Exception as e:
            logger.error(f"Beacon command failed: {e}")
            await self.bot.send_message(chat_id, f"⚠️ Beacon Status Unavailable: {e}")
