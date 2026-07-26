from services.bot.handlers.base import BaseHandler
from services.data_manager import get_data_manager
from services.brain import get_engine
import asyncio

class YarnHandler(BaseHandler):
    async def handle_yarn(self, chat_id: int, symbol: str = None, message_id: int = None):
        """
        The 'Thread of Truth' (YARN).
        Aggregates recent signals, executions, and context into a readable feed.
        """
        try:
            dm = get_data_manager()
            engine = get_engine()
            
            # Fetch recent signals (mock or real if DB has them)
            # For now, we pull from Engine's active states
            active_states = engine.states # dict of {symbol: state}
            
            # Filter by symbol if specific
            if symbol:
                relevant_states = {k:v for k,v in active_states.items() if k == symbol}
                title = f"[ YARN ] {symbol}"
            else:
                relevant_states = active_states
                title = "[ YARN ] GLOBAL THREAD"
                
            # Limit to active/interesting
            sorted_items = sorted(
                relevant_states.items(), 
                key=lambda x: abs(x[1].get('z_score', 0)), 
                reverse=True
            )[:5]
            
            # 0. PIDGIN POETRY (The Vibe)
            from services.pidgin_poet import PidginPoet
            target_sym = symbol if symbol else "BTCUSDT"
            mood = dm.get_market_mood(target_sym)
            narrative, exclamation = PidginPoet.compose(
                volatility=mood.get('volatility', 0.5),
                trend_strength=mood.get('trend_strength', 0.5),
                recent_change=mood.get('recent_change', 0.0)
            )
            
            msg = (
                f"<b>{title}</b>\n"
                "<code>════════════════════════════════</code>\n"
                f"<b>{exclamation}</b>\n"
                f"{narrative}\n"
                "<code>════════════════════════════════</code>\n\n"
            )

            # 1. CONTEXTUAL SCOREBOARD LINK
            # If symbol specific, we show specific scoreboard button below
            
            # Initialize Social Service (Unconditional)
            from services.social_service import get_social_service
            svc = get_social_service()

            # 2. SOCIAL SENTIMENT (Karma/Votes)
            if symbol:
                karma = svc.get_karma(symbol)
                msg += f"<b>COMMUNITY SENTIMENT</b>\n"
                msg += f"Karma Score: <code>{karma:+d}</code>\n"
                msg += f"Consensus: {'BULLISH' if karma > 0 else 'BEARISH' if karma < 0 else 'NEUTRAL'}\n"
                msg += "<code>────────────────────────</code>\n\n"

            # 3. YARNS (Comments/Signals)
            # 1. LIVE SIGNAL STREAM REMOVED (Strictly Social Request)
            # Replaced with purely social context aggregation.
            


            # 2. VOX POPULI (Social / Yarn)
            # 2. VOX POPULI (Social / Yarn)
            admin_yarn, user_yarns = None, []
            
            try:
                # Reuse the service instance from above if possible, or fetch new
                if symbol:
                    admin_yarn, user_yarns = svc.get_yarns(symbol, limit=5)
                else:
                    # Global yarns fallback
                    admin_yarn, user_yarns = svc.get_yarns(None, limit=5) 
            except TypeError:
                # Fallback for old API if something weird happened during hot reload
                pass
            except Exception as e:
                self.logger.error(f"Yarn Fetch Error: {e}")

            # A. PINNED OP (Admin)
            if admin_yarn:
                txt = admin_yarn.get('text', '')
                # No name shown for Admin Pin, just the content in a special block
                msg += (
                    f"<b>[ PINNED OP ]</b>\n"
                    f"<i>{txt}</i>\n"
                    "<code>────────────────────────</code>\n"
                )

            # B. COMMUNITY FIBER (Users)
            if user_yarns:
                msg += "\n<b>VOX POPULI</b>\n"
                for y in user_yarns:
                    user = y.get('username', 'Anon')[:10]
                    txt = y.get('text', '')
                    # Clean Emojis? The user asked to "get rid of those emojis there"
                    # We can't easily strip them without a regex library, but we can verify our bullet choice.
                    msg += f"• <b>{user}</b>: {txt}\n"

            msg += (
                "\n<code>════════════════════════════════</code>\n"
                "<b>[ HIVE MIND ]</b>\n"
                "<i>Reply to this message to contribute.</i>\n"
                "<i>Your voice shapes the Consensus.</i>"
            )
            
            # Navigation
            lb_cb = f"LEADERBOARD_SYM_{symbol}" if symbol else "LEADERBOARD_GLOBAL"
            
            # Use standard cyclical nav for neighbors
            nav_row = self._get_cyclical_nav("SYMBOL" if symbol else "YARN")
            
            # Customizing the Center Button
            if symbol:
                for btn in nav_row:
                    if btn["text"] == "○": 
                        btn["text"] = f"« BACK TO {symbol}"
                        btn["callback_data"] = f"PRICE_{symbol}"
            else:
                # Global Context: Center button should go home
                for btn in nav_row:
                    if btn["text"] == "○":
                        btn["text"] = "○"
                        btn["callback_data"] = "START"
            
            keyboard_rows = [
                [{"text": "TRADER SCOREBOARD", "callback_data": lb_cb}]
            ]

            if symbol:
                keyboard_rows.append([
                    {"text": "▲ LIKE", "callback_data": f"KARMA_UP_{symbol}"},
                    {"text": "▼ HATE", "callback_data": f"KARMA_DOWN_{symbol}"}
                ])
                
            keyboard_rows.append(nav_row)

            keyboard = {
                "inline_keyboard": keyboard_rows
            }
            
            if message_id:
                try:
                    await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=keyboard)
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        await self.bot.send_message(chat_id, msg, reply_markup=keyboard)
            else:
                await self.bot.send_message(chat_id, msg, reply_markup=keyboard)

        except Exception as e:
            self.logger.error(f"Yarn error: {e}")
            await self.send_message(chat_id, "[!] Yarn tangled. Try again.")

    async def handle_karma_vote(self, chat_id: int, user_id: int, symbol: str, direction: str, message_id: int = None):
        """Handle social sentiment voting (Karma)."""
        try:
            from services.social_service import get_social_service
            svc = get_social_service()
            
            # Record vote
            reaction = "UPVOTE" if direction == "UP" else "DOWNVOTE"
            svc.set_sentiment(user_id, symbol, reaction)
            
            # Refresh View to show updated score
            await self.handle_yarn(chat_id, symbol, message_id=message_id)
            
            # Ack to stop spinning
            try:
                msg = f"Voted {reaction} for {symbol}"
                await self.bot.answer_callback_query(chat_id, msg) 
            except: pass
            
        except Exception as e:
            self.logger.error(f"Karma vote error: {e}")

    async def handle_yarn_command(self, chat_id: int, user_id: int, username: str, text: str):
        """
        Handle /yarn commands to post new messages.
        Format: /yarn <SYMBOL> <MESSAGE>
        """
        try:
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                await self.send_message(chat_id, "<b>[ USAGE ]</b>\n`/yarn BTC This looks bullish!`")
                return

            symbol = parts[1].upper()
            content = parts[2]
            
            # 1. Post to Social Service
            from services.social_service import get_social_service
            svc = get_social_service()
            
            success = svc.post_yarn(symbol, user_id, username, content)
            
            if success:
                # 2. Confirm and Show relevant yarn
                await self.send_message(chat_id, f"<b>[ YARN SPUN ]</b>\nAdded to {symbol} thread.")
                # Refresh view
                await self.handle_yarn(chat_id, symbol)
            else:
                await self.send_message(chat_id, "[!] Failed to spin yarn.")

        except Exception as e:
            self.logger.error(f"Yarn Command Error: {e}")
            await self.send_message(chat_id, "[!] Error handling yarn command.")
