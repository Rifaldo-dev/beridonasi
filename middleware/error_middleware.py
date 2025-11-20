from common import get_logger, BotException, BanException, PendingDonationException, InvalidAmountException, QRISException

logger = get_logger(__name__)

class ErrorMiddleware:
    def __init__(self, bot):
        self.bot = bot
        self.register_error_handlers()

    def register_error_handlers(self):
        @self.bot.message_handler(func=lambda m: True)
        def handle_message_error(message):
            pass

    @staticmethod
    def handle_ban_error(bot, chat_id, user_id):
        logger.warning(f"Ban attempt - User {user_id}")
        bot.send_message(chat_id, "🚫 Anda telah diblacklist dan tidak dapat menggunakan sistem donasi.")

    @staticmethod
    def handle_pending_donation_error(bot, chat_id):
        logger.warning(f"Pending donation exists - Chat {chat_id}")
        bot.send_message(chat_id, "⚠️ Anda masih memiliki donasi yang belum selesai!")

    @staticmethod
    def handle_invalid_amount_error(bot, chat_id, message_id):
        try:
            bot.edit_message_text(
                "❌ Harga harus antara Rp 1.000 - Rp 1.000.000",
                chat_id, message_id
            )
        except:
            bot.send_message(chat_id, "❌ Harga harus antara Rp 1.000 - Rp 1.000.000")

    @staticmethod
    def handle_qris_error(bot, chat_id, message_id):
        try:
            bot.edit_message_text(
                "❌ **QRIS gagal!**\n\nSilakan coba lagi...",
                chat_id, message_id, parse_mode='Markdown'
            )
        except:
            bot.send_message(chat_id, "❌ QRIS gagal! Silakan coba lagi...")

    @staticmethod
    def handle_general_error(bot, chat_id, message_id=None, error_msg=""):
        error_text = f"❌ Terjadi kesalahan: {error_msg}" if error_msg else "❌ Terjadi kesalahan sistem!"
        try:
            if message_id:
                bot.edit_message_text(error_text, chat_id, message_id)
            else:
                bot.send_message(chat_id, error_text)
        except:
            pass
