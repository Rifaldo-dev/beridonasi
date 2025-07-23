import sqlite3
from telebot import types
from config import DATABASE_NAME, ADMIN_USER_ID, CHANNEL_ID, NOTIFICATION_CHANNEL, AUTO_DELETE_SUCCESS
from database import set_user_state, get_user_state, clear_user_state, ban_user, unban_user, is_banned
from utils import is_admin, auto_delete_message

def handle_donation_confirmation(bot, call, donation_qris_code):
    """Handle payment confirmation"""
    try:
        donation_id = int(call.data.split('_')[1])
        bot.answer_callback_query(call.id, "📨 Mengirim ke admin untuk verifikasi...")

        # Get donation details
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
        donation = cursor.fetchone()

        if not donation:
            bot.edit_message_text("❌ Donasi tidak ditemukan.", call.message.chat.id, call.message.message_id)
            conn.close()
            return

        # Update status to submitted
        cursor.execute('UPDATE donations SET status = ? WHERE id = ?', ('submitted', donation_id))
        conn.commit()
        conn.close()

        # Extract donation data
        (db_id, random_id, donor_name, message_text, amount, donation_item, 
         timestamp, status, qris_id, telegram_user_id, telegram_username) = donation

        # Format message untuk admin
        admin_text = f"""🔍 **VERIFIKASI DONASI**

🆔 **ID:** {random_id}
👤 **Donatur:** {donor_name if donor_name else 'Anonim'}
🎁 **Item:** {donation_item}
💰 **Nominal:** Rp {amount:,}
👤 **User ID:** {telegram_user_id}
🕐 **Waktu:** {timestamp}""".replace(',', '.')

        if message_text:
            admin_text += f"\n💬 **Pesan:** {message_text}"

        admin_text += "\n\n⚡ **Aksi Admin:**"

        # Add admin buttons
        admin_markup = types.InlineKeyboardMarkup()
        btn_approve = types.InlineKeyboardButton("✅ Setujui", callback_data=f"admin_approve_{donation_id}")
        btn_reject = types.InlineKeyboardButton("❌ Tolak", callback_data=f"admin_reject_{donation_id}")
        btn_ban = types.InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{telegram_user_id}")
        admin_markup.add(btn_approve, btn_reject)
        admin_markup.add(btn_ban)

        try:
            # Send to admin directly and channel
            bot.send_message(ADMIN_USER_ID, admin_text, parse_mode='Markdown', reply_markup=admin_markup)
            print(f"✅ Admin verification sent to user ID: {ADMIN_USER_ID}")

            # Also send to channel if different from admin direct message
            if CHANNEL_ID != ADMIN_USER_ID:
                bot.send_message(CHANNEL_ID, admin_text, parse_mode='Markdown', reply_markup=admin_markup)
                print(f"✅ Admin verification sent to channel ID: {CHANNEL_ID}")

        except Exception as e:
            print(f"❌ Failed to send admin verification: {e}")
            print(f"Admin ID: {ADMIN_USER_ID}, Channel ID: {CHANNEL_ID}")

        # Update user message
        try:
            bot.edit_message_caption(
                f"""✅ **DONASI TERKIRIM KE ADMIN**

{call.message.caption.split('**Cara Donasi:**')[0]}

📨 **Status:** Menunggu verifikasi admin
⏳ **Proses:** 1-5 menit
🔔 **Notifikasi:** Anda akan diberitahu hasilnya

Terima kasih atas kesabaran Anda! 💝""",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Failed to update user message: {e}")

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

def handle_admin_verification(bot, call):
    """Handle admin verification actions"""
    try:
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Akses ditolak!")
            return

        action = call.data.split('_')[1]

        if action == "approve":
            donation_id = int(call.data.split('_')[2])
            bot.answer_callback_query(call.id, "✅ Donasi disetujui!")

            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
            donation = cursor.fetchone()

            if donation:
                cursor.execute('UPDATE donations SET status = ? WHERE id = ?', ('approved', donation_id))
                conn.commit()

                # Extract donation data
                (db_id, random_id, donor_name, message_text, amount, donation_item, 
                 timestamp, status, qris_id, telegram_user_id, telegram_username) = donation

                # Create thank you image
                from main import create_thank_you_image
                thank_you_img = create_thank_you_image(donor_name, amount, donation_item)

                # Notify user with thank you image
                try:
                    if thank_you_img:
                        bot.send_photo(
                            telegram_user_id,
                            thank_you_img,
                            caption=f"✅ **DONASI DISETUJUI**\n\n🆔 {random_id}\n💰 Rp {amount:,}\n\n🎉 Terima kasih atas dukungan Anda!\n✨ Donasi telah diverifikasi admin.".replace(',', '.'),
                            parse_mode='Markdown'
                        )
                    else:
                        bot.send_message(
                            telegram_user_id,
                            f"✅ **DONASI DISETUJUI**\n\n🆔 {random_id}\n💰 Rp {amount:,}\n\n🎉 Terima kasih atas dukungan Anda!\n✨ Donasi telah diverifikasi admin.".replace(',', '.'),
                            parse_mode='Markdown'
                        )
                except:
                    pass

            conn.close()

            # Update admin message
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

            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
            donation = cursor.fetchone()

            if donation:
                cursor.execute('UPDATE donations SET status = ? WHERE id = ?', ('rejected', donation_id))
                conn.commit()

                # Notify user
                try:
                    bot.send_message(
                        donation[9],
                        f"❌ **DONASI DITOLAK**\n\n🆔 {donation[1]}\n💰 Rp {donation[4]:,}\n\n⚠️ Donasi Anda tidak dapat diverifikasi.\nSilakan coba lagi atau hubungi admin.".replace(',', '.'),
                        parse_mode='Markdown'
                    )
                except:
                    pass

            conn.close()

            # Update admin message
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

            ban_user(user_id, "", "Bermain-main dengan sistem donasi")

            # Notify banned user
            try:
                bot.send_message(user_id, "🚫 **ANDA TELAH DIBLACKLIST**\n\nAnda tidak dapat menggunakan sistem donasi.\nAlasan: Bermain-main dengan sistem donasi\n\n⚠️ Jangan bermain-main agar tidak di-blacklist!", parse_mode='Markdown')
            except:
                pass

            # Update admin message
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
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_collection')
def handle_cancel_collection_callback(call):
    try:
        bot.answer_callback_query(call.id, "❌ Dibatalkan")

        # Clear user state first
        clear_user_state(call.from_user.id)

        # Send cancellation message
        cancel_text = """❌ **DONASI DIBATALKAN**

✅ Proses donasi telah dibatalkan.
💡 Anda dapat memulai donasi baru kapan saja.

Gunakan `/donasi` untuk memulai donasi baru."""

        try:
            bot.edit_message_text(
                cancel_text,
                call.message.chat.id, 
                call.message.message_id,
                parse_mode='Markdown'
            )

            # Auto delete after 30 seconds
            auto_delete_message(bot, call.message.chat.id, call.message.message_id, 30)

        except Exception as edit_error:
            # If edit fails, try to delete and send new message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                cancel_msg = bot.send_message(call.message.chat.id, cancel_text, parse_mode='Markdown')
                auto_delete_message(bot, call.message.chat.id, cancel_msg.message_id, 30)
            except:
                pass

    except Exception as e:
        try:
            bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")
        except:
            pass