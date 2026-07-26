import os
import logging
from typing import Optional
from telegram.ext import Application

from config import get_settings

logger = logging.getLogger("TelegramBot")

class BaseTelegramBot:
    def __init__(self):
        settings = get_settings()
        self.settings = settings
        token_obj = settings.TELEGRAM_BOT_TOKEN
        self.token = token_obj.get_secret_value() if token_obj else None
        
        self.app: Optional[Application] = None
        self.running = False
        
        # Initialize whitelist from settings
        self.allowed_chat_ids = set()
        if settings.TELEGRAM_WHITELIST_IDS:
            try:
                ids = [int(i.strip()) for i in settings.TELEGRAM_WHITELIST_IDS.split(',') if i.strip()]
                self.allowed_chat_ids.update(ids)
                logger.info(f"Bot Whitelist Active: {len(self.allowed_chat_ids)} IDs")
            except Exception as e:
                logger.warning(f"Failed to parse TELEGRAM_WHITELIST_IDS: {e}")
