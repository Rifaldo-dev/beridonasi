import sqlite3
from telebot import types
from config import DATABASE_NAME, ADMIN_USER_ID, CHANNEL_ID, AUTO_DELETE_SUCCESS
from database import set_user_state, get_user_state, clear_user_state, ban_user, unban_user, is_banned
from common import is_admin, auto_delete_message, get_logger
from services import DonationService, UserService

logger = get_logger(__name__)

def handle_donation_confirmation(bot, call, donation_qris_code):
    try:
        donation_id = int(call.data.split('_')[1])
        bot.answer_callback_query(call.id, "📨 Mengirim ke admin untuk verifikasi...")

        donation_service = DonationService()
        donation = donation_service.get_donation(donation_id)

        if not donation:
            logger.warning(f"Donation {donation_id} not found")
            bot.edit_message_text("❌ Donasi tidak ditemukan.", call.message.chat.id, call.message.message_id)
            return

        donation_service.update_donation_status(donation_id, 'submitted')
        logger.info(f"Donation {donation_id} submitted for verification")

        db_id, random_id, donor_name, message_text, amount, donation_item, timestamp, status, qris_id, telegram_user_id, telegram_username = donation

        admin_text = f"""🔍 **VERIFIKASI DONASI**

🆔 **ID:** {random_id}
👤 **Donatur:** {donor_name if donor_name else 'Anonim'}
🎁 **Item:** {donation_item}
💰 **Nominal:** Rp {amount:,}
👤 **User ID:** {telegram_user_id}
🕐 **Waktu:** {timestamp}"""

        if message_text:
            admin_text += f"\n💬 **Pesan:** {message_text}"

        admin_text += "\n\n⚡ **Aksi Admin:**"
        admin_text = admin_text.replace(',', '.')

        admin_markup = types.InlineKeyboardMarkup()
        btn_approve = types.InlineKeyboardButton("✅ Setujui", callback_data=f"admin_approve_{donation_id}")
        btn_reject = types.InlineKeyboardButton("❌ Tolak", callback_data=f"admin_reject_{donation_id}")
        btn_ban = types.InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{telegram_user_id}")
        admin_markup.add(btn_approve, btn_reject)
        admin_markup.add(btn_ban)

        try:
            bot.send_message(ADMIN_USER_ID, admin_text, parse_mode='Markdown', reply_markup=admin_markup)
            logger.info(f"Admin verification sent to user ID: {ADMIN_USER_ID}")

            if CHANNEL_ID != ADMIN_USER_ID:
                bot.send_message(CHANNEL_ID, admin_text, parse_mode='Markdown', reply_markup=admin_markup)
                logger.info(f"Admin verification sent to channel ID: {CHANNEL_ID}")

        except Exception as e:
            logger.error(f"Failed to send admin verification: {e}")

        try:
            caption_parts = call.message.caption.split('**Cara Donasi:**') if call.message.caption else None
            if caption_parts:
                caption = caption_parts[0]
            else:
                caption = ""

            bot.edit_message_caption(
                f"""{caption}
📨 **Status:** Menunggu verifikasi admin
⏳ **Proses:** 1-5 menit
🔔 **Notifikasi:** Anda akan diberitahu hasilnya

Terima kasih atas kesabaran Anda! 💝""",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to update user message: {e}")

    except Exception as e:
        logger.error(f"Donation confirmation error: {e}")
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

def handle_admin_verification(bot, call):
    try:
        if not is_admin(call.from_user.id):
            logger.warning(f"Non-admin verification attempt from {call.from_user.id}")
            bot.answer_callback_query(call.id, "❌ Akses ditolak!")
            return

        donation_service = DonationService()
        user_service = UserService()
        action = call.data.split('_')[1]

        if action == "approve":
            donation_id = int(call.data.split('_')[2])
            bot.answer_callback_query(call.id, "✅ Donasi disetujui!")

            donation = donation_service.get_donation(donation_id)

            if donation:
                donation_service.update_donation_status(donation_id, 'approved')
                logger.info(f"Donation {donation_id} approved by admin {call.from_user.id}")

                db_id, random_id, donor_name, message_text, amount, donation_item, timestamp, status, qris_id, telegram_user_id, telegram_username = donation

                from main import create_thank_you_image
                thank_you_img = create_thank_you_image(donor_name, amount, donation_item)

                try:
                    amount_formatted = f"Rp {amount:,}".replace(',', '.')
                    if thank_you_img:
                        bot.send_photo(
                            telegram_user_id,
                            thank_you_img,
                            caption=f"✅ **DONASI DISETUJUI**\n\n🆔 {random_id}\n💰 {amount_formatted}\n\n🎉 Terima kasih atas dukungan Anda!\n✨ Donasi telah diverifikasi admin.",
                            parse_mode='Markdown'
                        )
                    else:
                        bot.send_message(
                            telegram_user_id,
                            f"✅ **DONASI DISETUJUI**\n\n🆔 {random_id}\n💰 {amount_formatted}\n\n🎉 Terima kasih atas dukungan Anda!\n✨ Donasi telah diverifikasi admin.",
                            parse_mode='Markdown'
                        )
                except:
                    pass

            conn.close()

            try:
                bot.edit_message_text(
                    f"✅ **DONASI DISETUJUI**\n\n{call.message.text}\n\n👤 Disetujui oleh: {call.from_user.first_name}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            except:
                pass

        elif action == "reject":
            donation_id = int(call.data.split('_')[2])
            bot.answer_callback_query(call.id, "❌ Donasi ditolak!")

            donation = donation_service.get_donation(donation_id)

            if donation:
                donation_service.update_donation_status(donation_id, 'rejected')
                logger.info(f"Donation {donation_id} rejected by admin {call.from_user.id}")

                try:
                    amount_formatted = f"Rp {donation[4]:,}".replace(',', '.')
                    bot.send_message(
                        donation[9],
                        f"❌ **DONASI DITOLAK**\n\n🆔 {donation[1]}\n💰 {amount_formatted}\n\n⚠️ Donasi Anda tidak dapat diverifikasi.\nSilakan coba lagi atau hubungi admin.",
                        parse_mode='Markdown'
                    )
                except:
                    pass

            try:
                bot.edit_message_text(
                    f"❌ **DONASI DITOLAK**\n\n{call.message.text}\n\n👤 Ditolak oleh: {call.from_user.first_name}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            except:
                pass

        elif action == "ban":
            user_id = int(call.data.split('_')[2])
            bot.answer_callback_query(call.id, "🚫 User di-ban!")

            user_service.ban_user(user_id, "", "Bermain-main dengan sistem donasi")
            logger.warning(f"User {user_id} banned by admin {call.from_user.id}")

            try:
                bot.send_message(user_id, "🚫 **ANDA TELAH DIBLACKLIST**\n\nAnda tidak dapat menggunakan sistem donasi.\nAlasan: Bermain-main dengan sistem donasi\n\n⚠️ Jangan bermain-main agar tidak di-blacklist!", parse_mode='Markdown')
            except:
                pass

            try:
                bot.edit_message_text(
                    f"🚫 **USER DI-BAN**\n\n{call.message.text}\n\n👤 Di-ban oleh: {call.from_user.first_name}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            except:
                pass

    except Exception as e:
        logger.error(f"Admin verification error: {e}")
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")
