import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from services.data_manager import get_data_manager, Subscription, UserBotSettings
from config import get_settings
import random

logger = logging.getLogger("SubscriptionManager")

class SubscriptionManager:
    """
    Manages user subscriptions for periodic updates.
    Handles add/remove logic and the background distribution loop.
    """
    def __init__(self):
        self.dm = get_data_manager()
        self.is_running = False
        
    async def start_loop(self):
        """Start the background check loop."""
        if self.is_running: return
        self.is_running = True
        logger.info("Subscription Manager: STARTED")
        asyncio.create_task(self._process_loop())

    def toggle_global_pause(self, user_id: int) -> bool:
        """Toggles pause state in DB. Returns True if PAUSED."""
        db = self.dm.SessionLocal()
        try:
            settings = db.query(UserBotSettings).filter(UserBotSettings.user_id == user_id).first()
            if not settings:
                settings = UserBotSettings(user_id=user_id, is_paused=1)
                db.add(settings)
                new_state = True
            else:
                settings.is_paused = 1 if settings.is_paused == 0 else 0
                new_state = (settings.is_paused == 1)
            
            db.commit()
            logger.info(f"User {user_id} global pause set to: {new_state}")
            return new_state
        except Exception as e:
            logger.error(f"Toggle pause failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def is_user_paused(self, user_id: int) -> bool:
        """Checks if a user is globally paused via DB."""
        db = self.dm.SessionLocal()
        try:
            settings = db.query(UserBotSettings).filter(UserBotSettings.user_id == user_id).first()
            return settings.is_paused == 1 if settings else False
        except Exception:
            return False
        finally:
            db.close()

    async def _process_loop(self):
        """Check for due subscriptions every minute."""
        while self.is_running:
            try:
                await self.process_subscriptions()
            except Exception as e:
                logger.error(f"Subscription loop error: {e}")
            
            # Check every minute
            await asyncio.sleep(60)

    def ensure_resumed(self, user_id: int, db: Session = None):
        """Ensures that global pause is OFF for the user."""
        should_close = False
        if db is None:
            db = self.dm.SessionLocal()
            should_close = True
        try:
            settings = db.query(UserBotSettings).filter(UserBotSettings.user_id == user_id).first()
            if settings and settings.is_paused == 1:
                settings.is_paused = 0
                db.commit()
                logger.info(f"User {user_id} notifications AUTO-RESUMED.")
        except Exception:
            db.rollback()
        finally:
            if should_close:
                db.close()

    async def process_subscriptions(self):
        """Finds due subscriptions and triggers delivery."""
        db = self.dm.SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Find Active subscriptions where last_sent + interval <= now
            # Optimization: SQL query logic
            # For simplicity in Python: Fetch all active, check time delta
            # Find Active subscriptions
            subs = db.query(Subscription).filter(Subscription.is_active == 1).all()
            
            # Efficiently fetch paused users from DB
            paused_settings = db.query(UserBotSettings).filter(UserBotSettings.is_paused == 1).all()
            paused_user_ids = {s.user_id for s in paused_settings}
            
            due_subs = []
            for sub in subs:
                # SKIP IF PAUSED
                if sub.user_id in paused_user_ids:
                    continue
                    
                next_run = sub.last_sent + timedelta(minutes=sub.interval_minutes)
                if now >= next_run:
                    due_subs.append(sub)
            
            if not due_subs:
                return

            logger.info(f"Processing {len(due_subs)} due subscriptions...")
            
            # Group by User to send AGGREGATED updates (Key Requirement)
            user_updates = {}
            
            for sub in due_subs:
                if sub.user_id not in user_updates:
                    user_updates[sub.user_id] = {
                        "chat_id": sub.chat_id,
                        "subs": []
                    }
                user_updates[sub.user_id]["subs"].append(sub)

            # Send Updates
            from services.bot.core import TelegramBot
            # We need the singleton instance if possible, or create a temporary one if designed that way.
            # However, core.py doesn't seem to export a 'get_bot' singleton accessor easily.
            # Looking at previous context, it seems the bot is instantiated in main.py.
            
            # CRITICAL FIX: The previous code tried `get_bot_application` which doesn't exist.
            # We need to bridge to the running bot instance.
            # Assuming 'bot' is accessible via some service locator or we instantiate a sender.
            # Strategies used in similar architectures:
            # 1. Instantiate a new TelegramBot just for sending (stateless for sending).
            # 2. Use a shared instance.
            
            # Since TelegramBot in core.py handles its own session and base_url, we can instantiate it.
            try:
                bot = TelegramBot()
            except Exception as e:
                logger.error(f"Failed to instantiate bot for notifications: {e}")
                return

            for user_id, data in user_updates.items():
                chat_id = data["chat_id"]
                sub_list = data["subs"]
                
                # Filter out Standalone types (OPPORTUNITIES)
                aggregated_subs = [s for s in sub_list if s.subscription_type != "OPPORTUNITIES"]
                opp_subs = [s for s in sub_list if s.subscription_type == "OPPORTUNITIES"]
                
                # 1. Handle Aggregated (NEWS, PRICE, CALENDAR)
                if aggregated_subs:
                    message_text = await self._generate_aggregated_message(aggregated_subs)
                    try:
                        await bot.send_message(chat_id, message_text)
                    except Exception as e:
                        logger.error(f"Failed to send aggregated sub to {chat_id}: {e}")
                    
                    # ALWAYS update last_sent so we don't spam if successful or failed (avoid infinite retry loops)
                    for sub in aggregated_subs:
                        sub.last_sent = now

                # 2. Handle Standalone (OPPORTUNITIES) - Simplified Logic
                for sub in opp_subs:
                    # Fire opportunities if due.
                    # We previously checked 'due_subs', so we know it's time.
                    try:
                        content = await self._fetch_content(sub.subscription_type, sub.target)
                        msg = (
                            f"<b>[ AURATIC OPPORTUNITY ]</b>\n"
                            f"<code>════════════════════</code>\n\n"
                            f"{content}\n"
                            f"<code>════════════════════</code>\n"
                            f"<i>Target: {sub.target}</i>"
                        )
                        await bot.send_message(chat_id, msg, parse_mode="HTML")
                        # CRITICAL: Update last_sent
                        sub.last_sent = now
                        logger.info(f"Sent opportunity to {user_id} for {sub.target}")
                    except Exception as e:
                        logger.error(f"Failed to send opportunity: {e}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Processing logic failed: {e}")
        finally:
            db.close()

    async def _generate_aggregated_message(self, subs):
        """Generates the HTML content for a list of due subscriptions."""
        header = (
            "<b>[ AURATIC INTELLIGENCE ]</b>\n"
            "<code>══════════════════════════════════════</code>\n"
        )
        body = ""
        
        for sub in subs:
            try:
                content = await self._fetch_content(sub.subscription_type, sub.target)
                body += f"\n<b>[+] {sub.subscription_type} [{sub.target}]</b>\n{content}\n"
            except Exception as e:
                logger.error(f"Content gen failed for {sub.id}: {e}")
                body += f"\n<b>[!] {sub.subscription_type}</b>\n<i>Update unavailable.</i>\n"

        footer = (
            "\n<code>══════════════════════════════════════</code>\n"
            "<i>To manage alerts, use /start > Menu</i>"
        )
        return header + body + footer

    async def _fetch_content(self, type, target):
        """Routes content generation based on type."""
        # This acts as a mini-handler
        if type == "NEWS":
            from services.news_aggregator import get_enhanced_news_aggregator
            agg = get_enhanced_news_aggregator()
            news = await agg.get_news_by_category(target, limit=2)
            if not news: return "<i>No recent headlines.</i>"
            lines = []
            for n in news:
                lines.append(f"· <a href='{n['url']}'>{n['title']}</a>")
            return "\n".join(lines)
            
        elif type == "PRICE":
            dm = get_data_manager()
            stats = dm.get_ticker_stats(target)
            if not stats: return "<i>Price Unavailable</i>"
            # Format mini ticker
            price = stats['price']
            chg = stats['change_pct']
            icon = "[UP]" if chg > 0 else "[DN]"
            return f"<code>{target} ${price:,.2f} {icon}{chg:+.2f}%</code>"
            
        elif type == "CALENDAR":
             from services.economic_calendar import get_economic_calendar
             cal = get_economic_calendar()
             events = await cal.get_upcoming_events(limit=3, sector_filter=target)
             if not events: return "<i>No upcoming events.</i>"
             return "\n".join([f"· {e['title'][:30]} [{e['impact'][:3]}]" for e in events])
             
        elif type == "OPPORTUNITIES":
            from services.opportunity_cache import get_opportunity_cache
            from services.aesthetic_service import ASCIIArt
            cache = get_opportunity_cache()
            all_opps = cache.get_all_opportunities()
            
            # Filter by target (or GLOBAL)
            if target and target != "GLOBAL":
                opps = [o for o in all_opps if o['symbol'] == target]
            else:
                opps = all_opps
            
            if not opps:
                return "<i>The universe is silent. No alpha detected.</i>"
                
            # Take top 1 or 2 for brevity
            top_opps = sorted(opps, key=lambda x: abs(x.get('alpha', 0)), reverse=True)[:2]
            lines = []
            for o in top_opps:
                symbol = o['symbol']
                signal = o.get('signal', 'NEUTRAL')
                alpha = o.get('alpha', 0)
                lines.append(f"<b>{symbol}</b> | {signal} (α: {alpha:.2f})")
            
            # Small Fractal
            seed_val = sum(ord(c) for c in (target or "GLOBAL"))
            fractal = ASCIIArt.generate_mandelbrot(
                width=24, height=5,
                zoom=1.0 + (seed_val % 10) * 0.05,
                center_x=-0.5, center_y=0
            )
            
            return f"<code>{fractal}</code>\n" + "\n".join(lines)
            
        return "<i>Content pending...</i>"

    # CRUD
    def add_subscription(self, user_id, chat_id, type, target, interval_minutes=60):
        db = self.dm.SessionLocal()
        try:
            # Check existing (Idempotency)
            exists = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.subscription_type == type,
                Subscription.target == target
            ).first()
            
            if exists:
                exists.interval_minutes = interval_minutes
                exists.is_active = 1
                logger.info(f"Updated subscription {exists.id} for user {user_id}")
            else:
                # Inherit interval from existing subscriptions to maintain user preference
                if interval_minutes == 60:
                    any_sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
                    if any_sub:
                        interval_minutes = any_sub.interval_minutes

                new_sub = Subscription(
                    user_id=user_id,
                    chat_id=chat_id,
                    subscription_type=type,
                    target=target,
                    interval_minutes=interval_minutes
                )
                db.add(new_sub)
                logger.info(f"Created subscription for user {user_id}")
            
            # AUTO-RESUME if they were paused
            self.ensure_resumed(user_id, db=db)
            
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Add Sub failed: {e}")
            return False
        finally:
            db.close()

    def remove_subscription(self, user_id, sub_id):
        db = self.dm.SessionLocal()
        try:
            sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.user_id == user_id).first()
            if sub:
                db.delete(sub)
                db.commit()
                return True
            return False
        finally:
            db.close()
            
    def get_user_subscriptions(self, user_id):
        db = self.dm.SessionLocal()
        try:
            subs = db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.is_active == 1).all()
            # Expunge to allow access after session close (Postgres workaround)
            for s in subs:
                db.expunge(s)
            return subs
        finally:
            db.close()

    def update_user_interval(self, user_id: int, new_interval_minutes: int):
        """Updates the interval for ALL active subscriptions of a user."""
        db = self.dm.SessionLocal()
        try:
            db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == 1
            ).update({"interval_minutes": new_interval_minutes})
            
            # AUTO-RESUME if they were paused
            self.ensure_resumed(user_id, db=db)
            
            db.commit()
            logger.info(f"Updated user {user_id} interval to {new_interval_minutes}m and RESUMED.")
        except Exception as e:
            logger.error(f"Failed to update interval: {e}")
            db.rollback()
        finally:
            db.close()

    async def preview_message(self, user_id: int) -> tuple[str, int]:
        """
        Returns (content_html, current_interval) for the user's dashboard.
        Returns ("No active subscriptions", 0) if none found.
        """
        subs = self.get_user_subscriptions(user_id)
        if not subs:
            return "<b>[!] No active subscriptions.</b>", 0
            
        # Get current interval from first sub (assuming sync)
        current_interval = subs[0].interval_minutes
        
        # Reuse the generation logic but specifically for preview
        return await self._generate_aggregated_message(subs), current_interval

# Singleton
_sub_manager = None
def get_subscription_manager():
    global _sub_manager
    if _sub_manager is None:
        _sub_manager = SubscriptionManager()
    return _sub_manager
