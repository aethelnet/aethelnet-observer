
import asyncio
import aiohttp
import logging
import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Set

from services.bot.router import CommandRouter

logger = logging.getLogger("TelegramBot")

class Job:
    def __init__(self, callback, interval, first, chat_id, name, data):
        self.callback = callback
        self.interval = interval
        self.chat_id = chat_id
        self.name = name
        self.data = data
        self._task = None

    def schedule_removal(self):
        if self._task:
            self._task.cancel()

class JobQueue:
    def __init__(self, bot):
        self.bot = bot
        self.jobs: List[Job] = []

    def run_repeating(self, callback, interval, first=0, chat_id=None, name=None, data=None):
        job = Job(callback, interval, first, chat_id, name, data)
        self.jobs.append(job)
        
        async def _loop():
            if first > 0: await asyncio.sleep(first)
            while True:
                try:
                    # Create a mock context for compatibility with PTB style jobs
                    class Context: pass
                    ctx = Context()
                    ctx.job = job
                    await callback(ctx)
                except Exception as e:
                    logging.getLogger("JobQueue").error(f"Job {name} error: {e}")
                await asyncio.sleep(interval)

        job._task = asyncio.create_task(_loop())
        return job

    def get_jobs_by_name(self, name):
        return [j for j in self.jobs if j.name == name]

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token)
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        port = os.getenv("PORT")
        if port:
            # Running in Cloud/Container -> Always prefer valid local loopback to avoid public DNS/NAT issues
            self.backend_url = f"http://localhost:{port}"
        else:
            # Local Dev -> Allow override or default to 8000
            self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        
        # Whitelist logic
        self.whitelist_enabled = os.getenv("TELEGRAM_BOT_WHITELIST_ENABLED", "false").lower() == "true"
        self.allowed_chat_ids: Set[int] = set()
        self._load_whitelist()
        
        # Affiliate IDs
        self.tradingview_affiliate_id = os.getenv("TRADINGVIEW_AFFILIATE_ID", "")
        self.binance_affiliate_id = os.getenv("BINANCE_AFFILIATE_ID", "")
        
        # Job Queue
        self.job_queue = JobQueue(self)

        # Default symbols
        self.default_symbols = ["BTCUSDT", "ETHUSDT", "XAUUSD", "EURUSD", "SPY", "QQQ"]

        self.router = CommandRouter(self)
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self.last_error: Optional[str] = None

    def _load_whitelist(self):
        try:
            allowed_ids_str = os.getenv("TELEGRAM_BOT_ALLOWED_CHAT_IDS", "")
            if allowed_ids_str:
                self.allowed_chat_ids = {int(id.strip()) for id in allowed_ids_str.split(",") if id.strip()}
            
            # Reset if whitelist disabled? No, keep them just in case logic changes
            if not self.allowed_chat_ids and self.whitelist_enabled:
                logger.warning("Whitelist enabled but no chat IDs provided!")
        except Exception as e:
            logger.error(f"Failed to load whitelist: {e}")

    async def start(self):
        """Alias for main.py compatibility"""
        await self.start_polling()

    async def start_polling(self):
        if not self.enabled:
            logger.warning("Bot disabled (no token).")
            return

        logger.info("Starting Telegram Bot (Modular Version)...")
        self._running = True
        self._session = aiohttp.ClientSession()
        
        offset = 0
        while self._running:
            try:
                updates = await self._get_updates(offset)
                for update in updates:
                    offset = update["update_id"] + 1
                    await self._handle_update(update)
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_error = f"Polling error: {str(e)} at {datetime.utcnow()}"
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)

    async def set_webhook(self, url: str) -> bool:
        if not self.enabled or not self.token: return False
        
        if not self._session: self._session = aiohttp.ClientSession()
        
        endpoint = f"{self.base_url}/setWebhook"
        try:
             async with self._session.post(endpoint, json={"url": url}, timeout=10) as resp:
                 if resp.status == 200:
                     data = await resp.json()
                     return data.get("ok", False)
        except Exception as e:
             logger.error(f"Webhook error: {e}")
        return False

    async def _get_updates(self, offset: int) -> List[Dict]:
        if not self._session: return []
        url = f"{self.base_url}/getUpdates"
        params = {"offset": offset, "timeout": 10}
        try:
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("result", [])
        except:
            pass
        return []

    async def _handle_update(self, update: Dict):
        message = update.get("message")
        callback_query = update.get("callback_query")
        
        if callback_query:
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            data = callback_query.get("data", "")
            user_id = callback_query.get("from", {}).get("id")
            message_id = callback_query.get("message", {}).get("message_id")
            
            if not chat_id: return
            
            try:
                # Whitelist check
                if self.whitelist_enabled and chat_id not in self.allowed_chat_ids:
                     await self.send_message(chat_id, "[ACCESS DENIED]")
                     return

                logger.info(f"Received callback: {data} from {chat_id}")
                
                # Dispatch to router
                await self.router.route_callback(data, chat_id, message_id, user_id)
                
                # Answer callback query to clear "loading" state in Telegram UI
                url = f"{self.base_url}/answerCallbackQuery"
                await self._session.post(url, json={"callback_query_id": callback_query["id"]})
            except Exception as e:
                logger.error(f"Callback processing failed: {e}", exc_info=True)
                # Try to answer anyway to stop spinner
                try:
                    url = f"{self.base_url}/answerCallbackQuery"
                    await self._session.post(url, json={"callback_query_id": callback_query["id"]})
                except: pass
            return

        if message:
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_id = message.get("from", {}).get("id")
            
            if not chat_id or not text: return
            
            try:
                # Whitelist check
                if self.whitelist_enabled and chat_id not in self.allowed_chat_ids:
                     logger.warning(f"Unauthorized access attempt from {chat_id}")
                     await self.send_message(chat_id, "[ACCESS DENIED] Device not authorized.")
                     return

                # Simple command parsing
                logger.info(f"Received message: {text} from {chat_id}")
                if text.startswith("/"):
                    parts = text.split()
                    command = parts[0]
                    args = parts[1:]
                    
                    # Extract username
                    username = message.get("from", {}).get("username", "Anon")
                    
                    # Dispatch to router
                    logger.info(f"Routing command: {command}")
                    await self.router.route_command(command, args, chat_id, user_id, username)
                else:
                    # Handle plain text (symbols, replies)
                    reply_to_message = message.get("reply_to_message")
                    username = message.get("from", {}).get("username", "Anon")
                    
                    await self.router.route_message(text, chat_id, user_id, username, reply_to_message)
            except Exception as e:
                logger.error(f"Message processing failed: {e}", exc_info=True)
                await self.send_message(chat_id, f"⚠️ Error processing command: {e}")

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML", include_donation: bool = False, reply_markup: Dict = None, disable_web_page_preview: bool = False):
        if not self._session or self._session.closed: 
            self._session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        # Donation button logic (only if no custom markup provided, to avoid conflict)
        elif include_donation:
            donation_url = os.getenv("TELEGRAM_DONATION_URL", "")
            if donation_url:
                payload["reply_markup"] = {
                    "inline_keyboard": [[{"text": "☕ Support Dev", "url": donation_url}]]
                }

        try:
             async with self._session.post(url, json=payload) as resp:
                 if resp.status != 200:
                     logger.error(f"Send failed: {await resp.text()}")
                 else:
                     return await resp.json() # Return response explicitly
        except Exception as e:
             logger.error(f"Send error: {e}")
             return None

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, parse_mode: str = "HTML", reply_markup: Dict = None, disable_web_page_preview: bool = False):
        if not self._session or self._session.closed: 
            self._session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        for attempt in range(2):
            try:
                async with self._session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        # Don't log "message is not modified" as error
                        err_text = await resp.text()
                        if "message is not modified" in err_text:
                            return None
                        
                        logger.error(f"Edit failed: {err_text}")
                        return None
                    return await resp.json()
            except (aiohttp.ClientConnectionError, aiohttp.ServerDisconnectedError) as e:
                if attempt == 0:
                    # Stale connection? Recreate session and retry
                     if self._session and not self._session.closed:
                         await self._session.close()
                     self._session = aiohttp.ClientSession()
                     continue
                logger.warning(f"Edit network error: {e}")
                return None
            except Exception as e:
                # Handle specific "Connection closed" text if not caught by types above
                if "Connection closed" in str(e) and attempt == 0:
                     if self._session and not self._session.closed:
                         await self._session.close()
                     self._session = aiohttp.ClientSession()
                     continue
                     
                logger.error(f"Edit error: {e}")
                return None

    async def delete_message(self, chat_id: int, message_id: int):
        if not self._session: self._session = aiohttp.ClientSession()
        url = f"{self.base_url}/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": message_id}
        try:
             async with self._session.post(url, json=payload) as resp:
                 return resp.status == 200
        except: return False

    async def send_photo(self, chat_id: int, photo: Any, caption: str = "", parse_mode: str = "HTML", reply_markup: Dict = None):
        if not self._session: self._session = aiohttp.ClientSession()
        
        # Multipart form data for photo upload
        url = f"{self.base_url}/sendPhoto"
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('caption', caption)
        data.add_field('parse_mode', parse_mode)
        
        if reply_markup:
            data.add_field('reply_markup', json.dumps(reply_markup))
            
        if isinstance(photo, bytes):
            data.add_field('photo', photo, filename='chart.png', content_type='image/png')
        elif hasattr(photo, 'read'): # File-like object
            data.add_field('photo', photo, filename='chart.png', content_type='image/png')
        else:
            data.add_field('photo', str(photo)) # URL or file_id
            
        try:
             async with self._session.post(url, data=data) as resp:
                 if resp.status != 200:
                     logger.error(f"Photo failed: {await resp.text()}")
                 return await resp.json()
        except Exception as e:
             logger.error(f"Photo error: {e}")
             return None

    async def fetch_api_data(self, endpoint: str) -> Any:
        # endpoint should be like "/api/..."
        url = f"{self.backend_url}{endpoint}"
        if not self._session: self._session = aiohttp.ClientSession()
        
        try:
             async with self._session.get(url, timeout=20) as resp:
                 if resp.status == 200:
                     return await resp.json()
                 else:
                     logger.error(f"API fetch failed {url}: Status {resp.status}")
                     # Optionally log response text for debugging
                     try:
                         text = await resp.text()
                         logger.debug(f"Error response body: {text[:200]}")
                     except:
                         pass
        except asyncio.TimeoutError:
             logger.error(f"API fetch TIMEOUT {url}")
        except Exception as e:
             logger.exception(f"API fetch CRASH {url}: {e}")
        return None

    async def check_backend_health(self) -> bool:
        try:
            res = await self.fetch_api_data("/")
            return res and res.get("status") == "operational"
        except:
            return False

    async def stop(self):
        self._running = False
        if self._session:
            await self._session.close()

    async def check_news_alerts(self, news_items: List[Dict]):
        """Placeholder for news alert checking logic."""
        logger.info(f"Checking {len(news_items)} news items for alerts...")

# Singleton logic used by older consumers
_singleton: Optional[TelegramBot] = None

def get_telegram_bot() -> TelegramBot:
    global _singleton
    if _singleton is None:
        _singleton = TelegramBot()
    return _singleton

# Compatibility Alias

# Internal Helper for Cross-Module Notifications
async def bot_internal_notify(message: str) -> bool:
    """
    Called by other modules (Execution, Brain) to send alerts.
    Uses the singleton bot instance.
    """
    try:
        bot = get_telegram_bot()
        if not bot.enabled: return False
        
        chat_id = bot.chat_id
        await bot.send_message(chat_id, message)
        return True
    except Exception as e:
        logger.error(f"[BOT-INTERNAL] Notify failed: {e}")
        return False
