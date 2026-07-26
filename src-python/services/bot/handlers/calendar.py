from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.economic_calendar import get_economic_calendar
from services.data_manager import get_data_manager
from services.brain import get_engine
import asyncio
from datetime import datetime
import logging
from services.bot.helpers.filters import BotIntelFilter

logger = logging.getLogger("TelegramBot")

# Sector keyword mapping for calendar events
CALENDAR_SECTOR_KEYWORDS = {
    "MACRO": ["GDP", "CPI", "FED", "INFLATION", "EMPLOYMENT", "INTEREST", "TREASURY", "PMI", "FOMC", "RATE", "PAYROLL", "CONSUMER"],
    "CRYPTO": ["BITCOIN", "CRYPTO", "ETF", "DIGITAL", "BLOCKCHAIN", "BTC", "ETHEREUM"],
    "TECH": ["TECH", "EARNINGS", "NASDAQ", "SILICON", "MANUFACTURING", "INDUSTRIAL"],
    "FOREX": ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD", "CURRENCY", "FOREX", "FX", "RATE DECISION", "CENTRAL BANK"],
}

class CalendarMixin:

    async def cmd_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str = "summary", page: int = 0, force_new: bool = False):
        await self._send_calendar(update, mode, page, force_new=force_new)

    def _get_auratic_analysis(self, event: dict) -> str:
        """Generate Auratic's live market context for an event."""
        try:
            engine = get_engine()
            dm = get_data_manager()
            title = event.get('title', '').upper()
            
            # Determine relevant symbol based on event type
            symbol = "BTCUSDT"
            if "ETHEREUM" in title or "ETH" in title:
                symbol = "ETHUSDT"
            
            state = engine._get_state(symbol)
            
            # Get live metrics
            z_score = state.get('current_z', 0)
            
            # Try to get current price change
            try:
                stats = dm.get_ticker_stats(symbol)
                change_pct = stats.get('change_pct', 0) if stats else 0
            except:
                change_pct = 0
            
            # Format trend
            if change_pct > 1:
                trend = f"+{change_pct:.1f}%"
            elif change_pct < -1:
                trend = f"{change_pct:.1f}%"
            else:
                trend = "FLAT"
            
            # Format Z-score
            if z_score > 0.5:
                z_status = f"Ψ={z_score:.2f} [OVERBOUGHT]"
            elif z_score < -2.0:
                z_status = f"Ψ={z_score:.2f} [OVERSOLD]"
            else:
                z_status = f"Ψ={z_score:.2f} [NEUTRAL]"
            
            # Simple ASCII format
            analysis = (
                f"<code>[*] AURATIC: {symbol[:3]} {trend} | {z_status}</code>"
            )
            return analysis
            
        except Exception as e:
            logger.debug(f"Auratic analysis skipped: {e}")
            return ""

    def _filter_events_by_sector(self, events: list, sector: str) -> list:
        """Filters events by sector keywords."""
        keywords = CALENDAR_SECTOR_KEYWORDS.get(sector.upper(), [])
        if not keywords:
            return events
        
        filtered = []
        for e in events:
            title_upper = (e.get('title', '') or '').upper()
            if any(kw in title_upper for kw in keywords):
                filtered.append(e)
        return filtered

    async def _send_calendar(self, update: Update, mode: str = "summary", page: int = 0, from_symbol: str = None, force_new: bool = False):
        print(f">>> _send_calendar called: mode={mode}, page={page}, force_new={force_new}", flush=True)
        message = update.effective_message
        try:
            # 1. SEND LOADING STATE
            header_pfx = "ECONOMIC"
            if mode != "summary": header_pfx = mode.upper()
            
            loading_text = f"<b>[ {header_pfx} CALENDAR ]</b>\n\n<code>Scanning global events timeline...</code>"
            target_msg = message
            
            if update.callback_query and not force_new:
                 await message.edit_text(loading_text, parse_mode="HTML")
            else:
                 target_msg = await message.reply_text(loading_text, parse_mode="HTML")

            cal = get_economic_calendar()
            await cal.fetch_calendar()
            
            all_events_raw = await cal.get_upcoming_events(limit=50)
            
            # Fetch User Style
            user_id = update.effective_user.id
            dm = get_data_manager()
            style = await asyncio.to_thread(dm.get_user_intel_style, user_id)
            simple_mode = await asyncio.to_thread(dm.get_user_simple_mode, user_id)
            
            # Apply Style Filter (ALL mode = no filtering)
            if simple_mode != 2:
                all_events = BotIntelFilter.filter_calendar(all_events_raw, style)
            else:
                all_events = all_events_raw
            
            # Apply filters based on mode
            if mode == "usd":
                all_events = [e for e in all_events if e['country'] == 'USD']
            elif mode.upper() in CALENDAR_SECTOR_KEYWORDS:
                all_events = self._filter_events_by_sector(all_events, mode)
            
            if not all_events:
                empty_msg = f"<b>[ {header_pfx} CALENDAR ]</b>\n\n<code>Timeline clear. No significant events.</code>"
                try: await target_msg.edit_text(empty_msg, parse_mode="HTML")
                except: pass
                return

            if mode == "summary":
                display_events = all_events[:5]
                header = "<b>[ CALENDAR SNAPSHOT ]</b>"
            else:
                ITEMS_PER_PAGE = 7
                start = page * ITEMS_PER_PAGE
                end = start + ITEMS_PER_PAGE
                display_events = all_events[start:end]
                
                mode_labels = {
                    "full": "FULL", "usd": "USD",
                    "macro": "MACRO", "crypto": "CRYPTO", "tech": "TECH"
                }
                label = mode_labels.get(mode.lower(), mode.upper())
                header = f"<b>[ {label} CALENDAR: PAGE {page+1} ]</b>"

            msg = f"{header}\n\n"
            current_date = ""

            for e in display_events:
                e_date = e['date']
                if e_date != current_date:
                    msg += f"<b>[DATE] {e_date}</b>\n"
                    current_date = e_date
                
                # Impact Map
                impact_map = {"High": "[!!!]", "Medium": "[!!]", "Low": "[!]"}
                icon = impact_map.get(e['impact'], "[*]")
                
                # Time Calculation
                try:
                    evt_dt = datetime.strptime(f"{e['date']} {e['time']}", "%Y-%m-%d %H:%M")
                    time_str = evt_dt.strftime('%H:%M')
                    
                    # Live check
                    diff = evt_dt - datetime.utcnow()
                    if diff.total_seconds() < 0 and diff.total_seconds() > -3600:
                        time_str = "LIVE"
                except:
                    time_str = e['time']

                msg += (
                    f"<code>{time_str} | {e['country']} {icon}</code>\n"
                    f"<b>{e['title']}</b>\n"
                    f"<code>Fcst: {e.get('forecast') or 'N/A'} | Prev: {e.get('previous') or 'N/A'}</code>\n"
                )
                
                # Add Auratic's unique AI analysis
                auratic_analysis = self._get_auratic_analysis(e)
                if auratic_analysis:
                    msg += f"{auratic_analysis}\n"
                
                msg += "<code>────────────────────────────────</code>\n"

            
            # Navigation
            buttons = []
            
            # Determine suffix for pagination
            suffix = f"_{from_symbol}" if from_symbol else ""
            
            if mode == "summary":
                # Sector navigation tabs
                buttons.append([
                    InlineKeyboardButton("MACRO [GDP]", callback_data=f"CALENDAR_MACRO_0{suffix}"),
                    InlineKeyboardButton("CRYPTO [BTC]", callback_data=f"CALENDAR_CRYPTO_0{suffix}"),
                    InlineKeyboardButton("FOREX [FX]", callback_data=f"CALENDAR_FOREX_0{suffix}"),
                ])
                buttons.append([
                    InlineKeyboardButton("FULL LIST [ALL]", callback_data=f"CALENDAR_FULL_0{suffix}"),
                    InlineKeyboardButton("USD ONLY [USA]", callback_data=f"CALENDAR_USD_0{suffix}")
                ])
            else:
                # Pagination
                nav_row = []
                if page > 0:
                    nav_row.append(InlineKeyboardButton("<< PREV", callback_data=f"CALENDAR_{mode.upper()}_{page-1}{suffix}"))
                if len(all_events) > (page + 1) * 5:
                    nav_row.append(InlineKeyboardButton("NEXT >>", callback_data=f"CALENDAR_{mode.upper()}_{page+1}{suffix}"))
                if nav_row: buttons.append(nav_row)
                
                # Sector shortcuts
                buttons.append([
                    InlineKeyboardButton("MACRO", callback_data=f"CALENDAR_MACRO_0{suffix}"),
                    InlineKeyboardButton("CRYPTO", callback_data=f"CALENDAR_CRYPTO_0{suffix}"),
                    InlineKeyboardButton("FOREX", callback_data=f"CALENDAR_FOREX_0{suffix}"),
                    InlineKeyboardButton("ALL", callback_data=f"CALENDAR_FULL_0{suffix}")
                ])
                buttons.append([InlineKeyboardButton("MINIMIZE [^]", callback_data=f"CALENDAR_SUMMARY_0{suffix}")])

            if from_symbol:
               buttons.append([InlineKeyboardButton(f"<< BACK [{from_symbol}]", callback_data=f"PRICE_{from_symbol}")])
            
            buttons.append([InlineKeyboardButton("○", callback_data="START")])

            reply_markup = InlineKeyboardMarkup(buttons)

            # Always update the target message (which is showing "Scanning...")
            try:
                await target_msg.edit_text(msg, parse_mode="HTML", reply_markup=reply_markup)
            except Exception as e:
                # If message content is identical, Telegram API raises an error. We ignore it.
                if "Message is not modified" not in str(e):
                    logger.error(f"Calendar Edit Error: {e}")
            
        except Exception as e:
            await message.reply_text(f"[ERROR] Calendar: {e}")
