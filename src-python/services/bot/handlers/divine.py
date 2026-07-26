import logging
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.brain import get_engine
from services.bot.fractal_weaver import FractalWeaver
from services.bot.fractal_weaver import FractalWeaver
from services.symbol_normalizer import get_symbol_normalizer
from services.episode_pattern_matcher import get_episode_pattern_matcher
from datetime import datetime

logger = logging.getLogger("DivineHandler")

class DivineHandler:
    def __init__(self, bot):
        self.bot = bot

    async def handle_divine(self, chat_id: int, symbol: str = None, message_id: int = None):
        """Displays advanced mathematical intelligence metrics for a symbol."""
        try:
            engine = get_engine()
            metrics = engine.get_divine_metrics(symbol)
            target_symbol = metrics.get('symbol', 'BTCUSDC')
            
            normalizer = get_symbol_normalizer()
            display_name = normalizer.to_display(target_symbol)
            
            # 1. Phase Mapping (Hilbert)
            phase = metrics.get('phase', 0.0)
            
            if phase < -2.5: 
                phase_tag = "[ABYSS]"
                phase_desc = "Bottom Cycle"
            elif phase < -0.5:
                phase_tag = "[ASCENT]"
                phase_desc = "Rising"
            elif phase < 0.5:
                phase_tag = "[ZENITH]"
                phase_desc = "Peak Approach"
            elif phase < 2.5:
                phase_tag = "[DESCENT]"
                phase_desc = "Falling"
            else:
                phase_tag = "[VORTEX]"
                phase_desc = "High Risk"

            # 2. DMD Forecast & Confidence
            dmd_val = metrics.get('dmd_forecast', 0.0)
            stability = metrics.get('stability', 0.0)
            confidence = 1.0 / (1.0 + (stability * 10)) if stability > 0 else 1.0
            confidence = max(0.1, min(0.99, confidence))
            
            # 3. Fractal Aesthetic
            weaver = FractalWeaver()
            import time
            seed = phase + (time.time() / 1000.0)
            fractal = weaver.generate_consciousness_fractal(32, 8, int(confidence * 100), seed)
            
            # 4. Text Assembly (No Emojis)
            mgr = getattr(engine, 'live_manager', None)
            pilot = getattr(mgr, 'active_avatar_key', 'rat').upper() if mgr else "RAT"
            auto = "ON" if (mgr and getattr(mgr, 'is_auto_pilot_active', False)) else "OFF"
            
            # 5. Dreamer Stats
            dreamer = get_episode_pattern_matcher()
            d_stats = dreamer.get_pattern_summary()
            dreamer_count = d_stats.get('pattern_count', 0)
            
            last_ts = d_stats.get('last_analysis')
            dreamer_time = "NEVER"
            if last_ts:
                try:
                    dt = datetime.fromisoformat(last_ts)
                    dreamer_time = dt.strftime("%H:%M:%S")
                except: pass
            
            t_stat = "DRIVING" if pilot == "DRAGON" else "WATCHING"
            v_stat = "DRIVING" if pilot == "SNAKE" else "BOOSTING"

            text = (
                f"<b>[ QUANTUM RESONANCE :: {display_name} ]</b>\n"
                f"<pre>{fractal}</pre>\n\n"
                f"<b>[ COUNCIL STATUS :: AUTO {auto} ]</b>\n"
                f"• PILOT ({pilot}) : <code>ACTIVE</code>\n"
                f"• TURTLE (TREND): <code>{t_stat}</code>\n"
                f"• ALCH (VOL)    : <code>{v_stat}</code>\n"
                f"• ARCH (RISK)   : <code>SHIELDING</code>\n\n"
                f"<b>CYCLE PHASE     :</b> <code>{phase_tag} {phase:.2f} rad</code>\n"
                f"<i>State: {phase_desc}</i>\n\n"
                f"<b>VECTOR PROJ     :</b> <code>{dmd_val:.2f}</code>\n"
                f"<b>STABILITY       :</b> <code>{stability:.6f}</code>\n"
                f"<b>CONFIDENCE      :</b> <code>{confidence*100:.1f}%</code>\n\n"
                f"<b>NETWORK DEPTH   :</b> <code>{metrics.get('esn_depth', 0.0):.4f}</code>\n"
                f"<b>GRAVITY         :</b> <code>{metrics.get('centrality', 0.0):.4f}</code>\n"
                f"<b>REGIME          :</b> <code>{metrics.get('regime', 'UNKNOWN')}</code>\n"
                f"<i>(Unknown = Calibrating History...)</i>\n\n"
                f"<b>[ THE DREAMER ]</b>\n"
                f"• PATTERNS      : <code>{dreamer_count}</code>\n"
                f"• LAST EPIPHANY : <code>{dreamer_time}</code>\n"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("REFRESH [SCAN]", callback_data=f"DIVINE_REFRESH_{target_symbol}"),
                    InlineKeyboardButton("STATISTICS", callback_data=f"STATS_{target_symbol}")
                ],
                [InlineKeyboardButton("FORCE EPIPHANY", callback_data=f"DIVINE_FORCE_{target_symbol}")],
                [InlineKeyboardButton("<< BACK TO MARKET", callback_data="PRICE_LANDING")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if message_id:
                try:
                    await self.bot.edit_message_text(chat_id, message_id, text, parse_mode="HTML", reply_markup=reply_markup.to_dict())
                except: pass
            else:
                await self.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup.to_dict())
        except Exception as e:
            logger.error(f"Error in handle_divine: {e}")
            error_text = "<b>[ERROR] Intelligence Link Severed.</b>\nCalculation Sync Failure."
            if message_id:
                await self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=error_text, parse_mode="HTML")
            else:
                await self.bot.send_message(chat_id=chat_id, text=error_text, parse_mode="HTML")
