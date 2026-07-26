import logging
import asyncio
from services.bot.handlers.base import BaseHandler
from services.subscription_manager import get_subscription_manager

logger = logging.getLogger("Handler.Subscription")

class SubscriptionHandler(BaseHandler):
    """
    Handles user interaction for Subscriptions.
    - Subscribe to News/Prices
    - Manage active subscriptions
    """
    
    async def handle_subscribe(self, chat_id: int, user_id: int, data: str):
        """
        Handle 'subscribe_TYPE_TARGET'
        """
        try:
            # Format: subscribe_TYPE_TARGET
            parts = data.split("_")
            if len(parts) < 3: return
            
            sub_type = parts[1]
            target = parts[2]
            
            sm = get_subscription_manager()
            success = sm.add_subscription(user_id, chat_id, sub_type, target, interval_minutes=60)
            
            if success:
                keyboard = {"inline_keyboard": [
                    [{"text": "MANAGE SUBS", "callback_data": "my_subscriptions"}],
                    [{"text": "○", "callback_data": "START"}]
                ]}
                await self.bot.send_message(chat_id, f"<b>[OK] Subscribed:</b> {sub_type} [{target}]", reply_markup=keyboard)
            else:
                await self.bot.send_message(chat_id, f"[!] Already subscribed or error.")
                
        except Exception as e:
            logger.error(f"Subscribe failed: {e}")
            await self.bot.send_message(chat_id, "[X] Error processing subscription.")

    async def handle_unsubscribe(self, chat_id: int, user_id: int, data: str, message_id: int = None, return_to_symbol: str = None):
        """
        Handle 'unsubscribe_SUBID'
        """
        try:
            # Format: unsubscribe_SUBID
            sub_id = data.split("_")[1]
            
            sm = get_subscription_manager()
            success = sm.remove_subscription(user_id, int(sub_id))
            
            if success:
                keyboard = {"inline_keyboard": [
                    [{"text": "○", "callback_data": "START"}]
                ]}
                await self.bot.send_message(chat_id, "<b>[OK] Alert dropped.</b>", reply_markup=keyboard)
            else:
                await self.bot.send_message(chat_id, "[!] Could not unsubscribe.")
                
        except Exception as e:
            logger.error(f"Unsubscribe failed: {e}")

    async def handle_manage_subscriptions(self, chat_id: int, user_id: int, message_id: int = None):
        """
        Show Subscription Dashboard with Live Preview and Interval Stepper.
        """
        try:
            sm = get_subscription_manager()
            subs = sm.get_user_subscriptions(user_id)
            
            if not subs:
                msg = (
                    "<b>[!] No active subscriptions.</b>\n\n"
                    "Browse <i>/news</i> or <i>/price</i> and select <b>[SUBSCRIBE]</b> to add alerts."
                )
                keyboard = {"inline_keyboard": [[{"text": "○", "callback_data": "START"}]]}
                
                if message_id:
                     await self.bot.edit_message_text(chat_id, message_id, msg, reply_markup=keyboard)
                else:
                     await self.send_markup(chat_id, msg, keyboard)
                return

            # Live Preview
            # Note: sm.preview_message expects user_id, returns (html, interval)
            preview_html, interval = await sm.preview_message(user_id)
            
            # Format Interval
            def fmt_interval(m):
                if m >= 1440: return f"{m//1440}d"
                if m >= 60: return f"{m//60}h"
                return f"{m}m"
                
            int_str = fmt_interval(interval)
            
            dash_header = (
                f"<b>[ SUBSCRIPTION DASHBOARD ]</b>\n"
                f"Frequency: <code>{int_str}</code>\n"
                f"Preview:\n"
                f"<code>────────────────────────────────</code>\n"
            )
            
            info_box = (
                f"\n<code>--------------------------------------</code>\n"
                f"[TIP] <b>Tip:</b> Toggling the center button (FREQ) will <b>PAUSE</b> all notification streams. "
                f"Use <b>[ - ]</b> / <b>[ + ]</b> to change how often you receive updates.\n"
                f"<i>For sound/mute settings, use your Telegram App settings.</i>"
            )
            
            full_text = dash_header + preview_html + info_box
            
            # Build Keyboard
            keyboard_rows = []
            
            # Row 1: Stepper
            is_paused = sm.is_user_paused(user_id)
            mid_text = "[ PAUSED ]" if is_paused else f"FREQ: {int_str}"
            
            keyboard_rows.append([
                {"text": "[ - ]", "callback_data": f"SUB_INT_DEC_{interval}"},
                {"text": mid_text, "callback_data": "TOGGLE_PAUSE"},
                {"text": "[ + ]", "callback_data": f"SUB_INT_INC_{interval}"}
            ])
            
            # Row 2+: Unsub
            for sub in subs:
                keyboard_rows.append([
                    {"text": f"[-] DROP {sub.target}", "callback_data": f"unsubscribe_{sub.id}"}
                ])
                
            keyboard_rows.append([{"text": "○", "callback_data": "START"}])
            
            reply_markup = {"inline_keyboard": keyboard_rows}
            
            if message_id:
                await self.bot.edit_message_text(chat_id, message_id, full_text, reply_markup=reply_markup)
            else:
                await self.send_markup(chat_id, full_text, reply_markup)

        except Exception as e:
            logger.error(f"Manage Subs failed: {e}")
            await self.bot.send_message(chat_id, "[X] Dashboard Error.")

    async def handle_interval_adjust(self, chat_id: int, user_id: int, data: str, message_id: int = None):
        """
        Handle [ - ] / [ + ] interval adjustments.
        STEPS: 15, 60, 180, 720, 1440, 4320, 10080, 20160
        """
        try:
            # Format: SUB_INT_DEC_60
            parts = data.split("_")
            direction = parts[2] # DEC or INC
            current_val = int(parts[3])
            
            STEPS = [15, 60, 180, 720, 1440, 4320, 10080, 20160]
            
            try:
                idx = STEPS.index(current_val)
            except ValueError:
                idx = min(range(len(STEPS)), key=lambda i: abs(STEPS[i]-current_val))
                
            new_idx = idx
            if direction == "INC":
                new_idx = min(len(STEPS)-1, idx + 1)
            elif direction == "DEC":
                new_idx = max(0, idx - 1)
                
            new_interval = STEPS[new_idx]
            
            if new_interval != current_val:
                sm = get_subscription_manager()
                sm.update_user_interval(user_id, new_interval)
                # Refresh
                await self.handle_manage_subscriptions(chat_id, user_id, message_id)
            else:
                # No change (limit reached), just refresh or ignore
                pass
                
        except Exception as e:
            logger.error(f"Interval adjust failed: {e}")

    async def handle_toggle_pause(self, chat_id: int, user_id: int, message_id: int = None):
        """Toggle Global Pause"""
        try:
            sm = get_subscription_manager()
            sm.toggle_global_pause(user_id)
            await self.handle_manage_subscriptions(chat_id, user_id, message_id)
        except Exception as e:
            logger.error(f"Pause error: {e}")
