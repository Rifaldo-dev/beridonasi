from common import get_logger, BotException

logger = get_logger(__name__)

class LoggerMiddleware:
    def __init__(self, bot):
        self.bot = bot
        self.register_handlers()

    def register_handlers(self):
        @self.bot.message_handler(func=lambda m: True, content_types=['text'])
        def log_message(message):
            logger.info(f"Message from {message.from_user.id} (@{message.from_user.username}): {message.text[:50]}")

        @self.bot.callback_query_handler(func=lambda c: True)
        def log_callback(call):
            logger.info(f"Callback from {call.from_user.id} (@{call.from_user.username}): {call.data[:50]}")

    @staticmethod
    def log_donation(user_id, username, amount, status):
        logger.info(f"Donation [{status}] - User: {user_id} (@{username}), Amount: Rp {amount:,}")

    @staticmethod
    def log_ban(user_id, username, reason):
        logger.warning(f"User banned - ID: {user_id}, Username: @{username}, Reason: {reason}")

    @staticmethod
    def log_error(error, context=""):
        logger.error(f"Error [{context}]: {str(error)}", exc_info=True)

    @staticmethod
    def log_admin_action(admin_id, action, details):
        logger.warning(f"Admin action - Admin: {admin_id}, Action: {action}, Details: {details}")
