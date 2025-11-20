from telebot import types
from decorators import admin_required
from core import SessionLocal
from repositories import UserRepository, DonationRepository
from common import is_admin, auto_delete_message, _format_amount, get_logger
from config import ADMIN_USER_ID

logger = get_logger(__name__)

def register_admin_routes(bot):
    
    @bot.message_handler(commands=['ban'])
    @admin_required
    def ban_user_command(message):
        try:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "❌ Format: `/ban <user_id> [reason]`", parse_mode='Markdown')
                return

            user_id = int(args[1])
            reason = " ".join(args[2:]) if len(args) > 2 else "Bermain-main dengan sistem donasi"

            db = SessionLocal()
            UserRepository.ban_user(db, user_id, "", reason)
            db.close()
            
            logger.warning(f"User {user_id} banned by admin {message.from_user.id}. Reason: {reason}")
            bot.reply_to(message, f"✅ User {user_id} telah di-ban!\nAlasan: {reason}")

            try:
                bot.send_message(user_id, f"🚫 **ANDA TELAH DIBLACKLIST**\n\nAnda tidak dapat menggunakan sistem donasi.\nAlasan: {reason}\n\n⚠️ Jangan bermain-main agar tidak di-blacklist!", parse_mode='Markdown')
            except:
                pass

        except ValueError:
            bot.reply_to(message, "❌ User ID harus berupa angka!")
        except Exception as e:
            logger.error(f"Ban command error: {e}")
            bot.reply_to(message, f"❌ Error: {str(e)}")

    @bot.message_handler(commands=['unban'])
    @admin_required
    def unban_user_command(message):
        try:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "❌ Format: `/unban <user_id>`", parse_mode='Markdown')
                return

            user_id = int(args[1])

            db = SessionLocal()
            if UserRepository.unban_user(db, user_id):
                logger.warning(f"User {user_id} unbanned by admin {message.from_user.id}")
                bot.reply_to(message, f"✅ User {user_id} telah di-unban!")

                try:
                    bot.send_message(user_id, "✅ **ANDA TELAH DI-UNBAN**\n\nAnda kini dapat menggunakan sistem donasi kembali.\n\n⚠️ Harap gunakan dengan bijak!", parse_mode='Markdown')
                except:
                    pass
            else:
                bot.reply_to(message, f"❌ User {user_id} tidak ditemukan dalam daftar ban.")
            db.close()

        except ValueError:
            bot.reply_to(message, "❌ User ID harus berupa angka!")
        except Exception as e:
            logger.error(f"Unban command error: {e}")
            bot.reply_to(message, f"❌ Error: {str(e)}")

    @bot.message_handler(commands=['banlist'])
    @admin_required
    def list_banned_users(message):
        try:
            db = SessionLocal()
            banned_users = UserRepository.get_banned_users(db)
            db.close()

            if not banned_users:
                bot.reply_to(message, "✅ Tidak ada user yang di-ban.")
                return

            ban_text = "🚫 **Daftar User yang Di-ban:**\n\n"
            for banned_user in banned_users:
                username_display = f"@{banned_user.username}" if banned_user.username else "Unknown"
                ban_text += f"• **{banned_user.user_id}** ({username_display})\n"
                ban_text += f"  📅 {banned_user.banned_at}\n"
                ban_text += f"  💬 {banned_user.reason}\n\n"

            bot.reply_to(message, ban_text, parse_mode='Markdown')
            logger.info(f"Ban list viewed by admin {message.from_user.id}")

        except Exception as e:
            logger.error(f"Ban list error: {e}")
            bot.reply_to(message, f"❌ Error: {str(e)}")

    @bot.message_handler(commands=['testadmin'])
    def test_admin_connection(message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Hanya admin yang dapat melakukan test.")
            return

        test_text = f"""🔧 **Test Koneksi Admin**

✅ Bot dapat mengirim pesan ke admin
👤 Admin ID: {ADMIN_USER_ID}
👤 Your ID: {message.from_user.id}
✅ Admin Status: {'YES' if is_admin(message.from_user.id) else 'NO'}

Semua sistem berjalan normal! 🤖"""

        bot.reply_to(message, test_text, parse_mode='Markdown')
        
        try:
            bot.send_message(ADMIN_USER_ID, f"🔧 Test message from bot - Your ID: {message.from_user.id}")
            bot.reply_to(message, "✅ Test message sent to admin ID successfully!")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send test message: {e}")
