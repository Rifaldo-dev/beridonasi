from functools import wraps
from config import ADMIN_USER_ID
from common import get_logger

logger = get_logger(__name__)

def admin_required(func):
    @wraps(func)
    def wrapper(bot, message, *args, **kwargs):
        if message.from_user.id != ADMIN_USER_ID:
            logger.warning(f"Non-admin access attempt from {message.from_user.id} to {func.__name__}")
            bot.reply_to(message, "❌ Hanya admin yang dapat menggunakan command ini.")
            return
        return func(bot, message, *args, **kwargs)
    return wrapper
