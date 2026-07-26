
"""
Legacy Telegram Bot Wrapper.
Redirects to the new modular implementation in services.bot.core
"""
import logging
from services.bot.core import TelegramBot, get_telegram_bot as _get_core_bot

# Re-export for compatibility
TelegramBot = TelegramBot

def get_telegram_bot() -> TelegramBot:
    return _get_core_bot()

# Adapter for MinimalBotService if needed (main.py compatibility)
# If main.py expects MinimalBotService class, we can alias it or mock it.
# But main.py lines 1825-1931 in original file were "Adapter".
# If main.py imports MinimalBotService from here, we need it.
# Let's check main.py imports again.
# main.py imports `from services.bot.core import get_telegram_bot`.
# So main.py doesn't use this file anymore?
# If main.py uses bot.core, then this file is only for other legacy consumers.
# Safest is to just re-export.
