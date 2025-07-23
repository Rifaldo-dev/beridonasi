
#!/usr/bin/env python3
"""
Donation Bot - aldo soft
A Telegram bot for donation system with QRIS payment verification
"""

import telebot
import signal
import sys
import time
from telebot import types
import sqlite3
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
import string
import threading

# Import modules
from config import BOT_TOKEN, ADMIN_USER_ID, CHANNEL_ID, NOTIFICATION_CHANNEL, DONATION_ITEMS, AUTO_DELETE_DONATION, DATABASE_NAME
from database import init_db, load_donation_qris, is_banned, has_pending_donation, ban_user, unban_user, add_custom_donation_item, get_all_donation_items, set_user_state, get_user_state, clear_user_state
from utils import is_admin, generate_random_id, generate_qris, create_donation_sticker, auto_delete_message, get_random_donation_item
from handlers.commands import welcome_command, setup_qris_command, start_donation_command, custom_donation_command, stats_command
from handlers.callbacks import handle_donation_confirmation, handle_admin_verification

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Global variable for QRIS
donation_qris_code = None

def signal_handler(sig, frame):
    """Handle graceful shutdown"""
    print("\n🛑 Shutting down donation bot...")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Command Handlers
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_command(bot, message)

@bot.message_handler(commands=['setupqris'])
def handle_setup_qris(message):
    setup_qris_command(bot, message)

@bot.message_handler(commands=['donasi', 'donate'])
def handle_donation(message):
    start_donation_command(bot, message)

@bot.message_handler(commands=['beri'])
def handle_custom_donation(message):
    custom_donation_command(bot, message)

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    stats_command(bot, message)

@bot.message_handler(commands=['add'])
def handle_add_item(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ **HANYA ADMIN YANG DAPAT MENAMBAH ITEM**\n\nCommand `/add` hanya dapat digunakan oleh admin.", parse_mode='Markdown')
        return

    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ Format: `/add <nama_item> <harga>`\nContoh: `/add bakso 10000`", parse_mode='Markdown')
            return

        item_name = args[1].lower()
        price_str = args[2]

        if not price_str.isdigit():
            bot.reply_to(message, "❌ Harga harus berupa angka!\nContoh: `/add bakso 10000`", parse_mode='Markdown')
            return

        price = int(price_str)

        if price < 1000:
            bot.reply_to(message, "❌ Harga minimal Rp 1.000")
            return

        if price > 1000000:
            bot.reply_to(message, "❌ Harga maksimal Rp 1.000.000")
            return

        # Add emoji based on item name
        item_emoji = ""
        if any(food in item_name for food in ["bakso", "mie", "nasi", "soto", "gado"]):
            item_emoji = "🍜"
        elif any(drink in item_name for drink in ["kopi", "teh", "jus", "air"]):
            item_emoji = "☕"
        elif any(snack in item_name for snack in ["kerupuk", "chips", "kue", "roti"]):
            item_emoji = "🍪"
        else:
            item_emoji = "🎁"

        item_with_emoji = f"{item_emoji} {item_name}"

        # Save to database
        add_custom_donation_item(item_with_emoji, price, message.from_user.id)

        success_msg = bot.reply_to(message, f"✅ Item donasi berhasil ditambahkan!\n\n🎁 **{item_with_emoji}**\n💰 Rp {price:,}\n\nSekarang item ini bisa muncul saat donasi random!".replace(',', '.'))

        # Auto-delete after 30 seconds
        auto_delete_message(bot, message.chat.id, success_msg.message_id, 30)
        auto_delete_message(bot, message.chat.id, message.message_id, 30)

    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan: {str(e)}")

@bot.message_handler(commands=['listitem'])
def handle_list_items(message):
    try:
        from config import DONATION_ITEMS

        items_text = "🎁 **DAFTAR ITEM DONASI**\n\n"
        items_text += "📦 **Item Default:**\n"

        for category, items in DONATION_ITEMS.items():
            items_text += f"\n🏷️ **{category.title()}:**\n"
            for item in items[:5]:
                items_text += f"  • {item}\n"
            if len(items) > 5:
                items_text += f"  • ... dan {len(items)-5} lainnya\n"

        # Get custom items
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT item_name, price, created_at FROM custom_donation_items ORDER BY created_at DESC')
        custom_items = cursor.fetchall()
        conn.close()

        if custom_items:
            items_text += "\n🎨 **Item Custom (Admin):**\n"
            for item_name, price, created_at in custom_items[:10]:
                items_text += f"  • {item_name} - Rp {price:,}\n"
            if len(custom_items) > 10:
                items_text += f"  • ... dan {len(custom_items)-10} item lainnya\n"

        items_text += f"\n📊 **Total Items:** {sum(len(items) for items in DONATION_ITEMS.values()) + len(custom_items)} item\n"
        items_text += f"🎲 **System:** Item dipilih secara random saat donasi"

        if is_admin(message.from_user.id):
            items_text += f"\n\n⚙️ **Admin Commands:**\n"
            items_text += f"• `/add <item> <harga>` - Tambah item custom"
            items_text += f"• `/itemlist` - Detail item custom"

        items_text = items_text.replace(',', '.')

        list_msg = bot.reply_to(message, items_text, parse_mode='Markdown')
        auto_delete_message(bot, message.chat.id, list_msg.message_id, 120)
        auto_delete_message(bot, message.chat.id, message.message_id, 30)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT id, random_id, amount FROM donations WHERE telegram_user_id = ? AND status IN ("pending", "submitted")', (message.from_user.id,))
        active_donation = cursor.fetchone()

        if not active_donation:
            bot.reply_to(message, "✅ Anda tidak memiliki donasi aktif.")
            conn.close()
            return

        donation_id, random_id, amount = active_donation

        cursor.execute('UPDATE donations SET status = ? WHERE id = ?', ('cancelled', donation_id))
        conn.commit()
        conn.close()

        clear_user_state(message.from_user.id)

        cancel_msg = bot.reply_to(message, f"✅ **Donasi Dibatalkan**\n\n🆔 {random_id}\n💰 Rp {amount:,}\n\nAnda sekarang dapat membuat donasi baru.".replace(',', '.'), parse_mode='Markdown')
        auto_delete_message(bot, message.chat.id, cancel_msg.message_id, 30)
        auto_delete_message(bot, message.chat.id, message.message_id, 30)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Hanya admin yang dapat melakukan ban.")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Format: `/ban <user_id> [reason]`", parse_mode='Markdown')
            return

        user_id = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "Bermain-main dengan sistem donasi"

        ban_user(user_id, "", reason)
        bot.reply_to(message, f"✅ User {user_id} telah di-ban!\nAlasan: {reason}")

        # Notify banned user
        try:
            bot.send_message(user_id, f"🚫 **ANDA TELAH DIBLACKLIST**\n\nAnda tidak dapat menggunakan sistem donasi.\nAlasan: {reason}\n\n⚠️ Jangan bermain-main agar tidak di-blacklist!", parse_mode='Markdown')
        except:
            pass

    except ValueError:
        bot.reply_to(message, "❌ User ID harus berupa angka!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Hanya admin yang dapat melakukan unban.")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Format: `/unban <user_id>`", parse_mode='Markdown')
            return

        user_id = int(args[1])

        if unban_user(user_id):
            bot.reply_to(message, f"✅ User {user_id} telah di-unban!")

            # Notify unbanned user
            try:
                bot.send_message(user_id, "✅ **ANDA TELAH DI-UNBAN**\n\nAnda kini dapat menggunakan sistem donasi kembali.\n\n⚠️ Harap gunakan dengan bijak!", parse_mode='Markdown')
            except:
                pass
        else:
            bot.reply_to(message, f"❌ User {user_id} tidak ditemukan dalam daftar ban.")

    except ValueError:
        bot.reply_to(message, "❌ User ID harus berupa angka!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['itemlist'])
def list_custom_items(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Hanya admin yang dapat melihat daftar item custom.")
        return

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT item_name, price, created_at, created_by FROM custom_donation_items ORDER BY created_at DESC')
        custom_items = cursor.fetchall()
        conn.close()

        if not custom_items:
            bot.reply_to(message, "✅ Belum ada item custom yang ditambahkan.")
            return

        items_text = "🎁 **Daftar Item Donasi Custom:**\n\n"
        for item_name, price, created_at, created_by in custom_items:
            items_text += f"• **{item_name}** - Rp {price:,}\n"
            items_text += f"  📅 {created_at} | 👤 {created_by}\n\n"

        items_text = items_text.replace(',', '.')
        bot.reply_to(message, items_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['banlist'])
def list_banned_users(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Hanya admin yang dapat melihat daftar ban.")
        return

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, banned_at, reason FROM banned_users ORDER BY banned_at DESC')
        banned_users = cursor.fetchall()
        conn.close()

        if not banned_users:
            bot.reply_to(message, "✅ Tidak ada user yang di-ban.")
            return

        ban_text = "🚫 **Daftar User yang Di-ban:**\n\n"
        for user_id, username, banned_at, reason in banned_users:
            username_display = f"@{username}" if username else "Unknown"
            ban_text += f"• **{user_id}** ({username_display})\n"
            ban_text += f"  📅 {banned_at}\n"
            ban_text += f"  💬 {reason}\n\n"

        bot.reply_to(message, ban_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['testadmin'])
def test_admin_connection(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Hanya admin yang dapat melakukan test.")
        return

    test_text = f"""🔧 **Test Koneksi Admin**

✅ Bot dapat mengirim pesan ke admin
👤 Admin ID: {ADMIN_USER_ID}
📱 Channel ID: {CHANNEL_ID}
🔔 Notification Channel: {NOTIFICATION_CHANNEL}
👤 Your ID: {message.from_user.id}
✅ Admin Status: {'YES' if is_admin(message.from_user.id) else 'NO'}

Semua sistem berjalan normal! 🤖"""

    bot.reply_to(message, test_text, parse_mode='Markdown')
    
    # Test sending message to admin ID directly
    try:
        bot.send_message(ADMIN_USER_ID, f"🔧 Test message from bot - Your ID: {message.from_user.id}")
        bot.reply_to(message, "✅ Test message sent to admin ID successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to send test message: {e}")

# Message handler for QRIS setup
@bot.message_handler(func=lambda message: get_user_state(message.from_user.id)['state'] == 'setup_qris')
def collect_qris_code(message):
    try:
        if not is_admin(message.from_user.id):
            return
            
        user_state = get_user_state(message.from_user.id)
        qris_code = message.text.strip()
        
        # Delete user message
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        # Validate QRIS format
        if len(qris_code) < 50 or not qris_code.startswith('00020'):
            bot.edit_message_text(
                "❌ **QRIS tidak valid!**\n\nPastikan QRIS code lengkap dan benar.\n\nSilakan coba lagi...",
                user_state['data']['chat_id'],
                user_state['data']['message_id'], 
                parse_mode='Markdown'
            )
            return
        
        # Test QRIS generation
        test_qris = generate_qris(qris_code, 1000)
        if not test_qris:
            bot.edit_message_text(
                "❌ **QRIS gagal ditest!**\n\nQRIS tidak dapat digunakan untuk generate payment.\n\nSilakan coba dengan QRIS lain...",
                user_state['data']['chat_id'],
                user_state['data']['message_id'],
                parse_mode='Markdown'
            )
            return
        
        # Save QRIS
        from database import save_donation_qris
        save_donation_qris(qris_code)
        
        # Update global variable
        global donation_qris_code
        donation_qris_code = qris_code
        
        clear_user_state(message.from_user.id)
        
        success_text = f"""✅ **QRIS Setup Berhasil!**

🔐 QRIS code telah disimpan dan siap digunakan.
🧪 Test generation berhasil.
💫 Sistem donasi sekarang aktif!

⚡ **Status:** Ready untuk menerima donasi
🎯 **Test Amount:** Rp 1.000 ✅

Bot siap digunakan! 🚀"""
        
        bot.edit_message_text(
            success_text,
            user_state['data']['chat_id'],
            user_state['data']['message_id'],
            parse_mode='Markdown'
        )
        
        # Auto delete after 30 seconds
        auto_delete_message(bot, user_state['data']['chat_id'], user_state['data']['message_id'], 30)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Setup error: {str(e)}")
        clear_user_state(message.from_user.id)

# Message Handlers for User States
@bot.message_handler(func=lambda message: get_user_state(message.from_user.id)['state'] == 'collecting_name')
def collect_donor_name(message):
    try:
        user_state = get_user_state(message.from_user.id)
        donor_name = message.text.strip()[:20]

        user_state['data']['donor_name'] = donor_name
        set_user_state(message.from_user.id, 'collecting_message', user_state['data'])

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        message_markup = types.InlineKeyboardMarkup()
        btn_skip_message = types.InlineKeyboardButton("⏭️ Skip Pesan", callback_data=f"skip_message_{user_state['data']['amount']}")
        btn_cancel = types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_collection")
        message_markup.add(btn_skip_message)
        message_markup.add(btn_cancel)

        message_text = f"""💝 **Donasi Rp {user_state['data']['amount']:,}**
👤 **Nama:** {donor_name}

📝 **Langkah 2/2: Masukkan Pesan (Opsional)**

Ketik pesan yang ingin ditampilkan.
Contoh: `Terima kasih atas karya yang luar biasa!`

💡 Atau klik "Skip" jika tidak ingin menambah pesan.""".replace(',', '.')

        bot.edit_message_text(message_text, user_state['data']['chat_id'], user_state['data']['message_id'], parse_mode='Markdown', reply_markup=message_markup)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        clear_user_state(message.from_user.id)

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id)['state'] == 'collecting_message')
def collect_donor_message(message):
    try:
        user_state = get_user_state(message.from_user.id)
        donor_message = message.text.strip()[:100]

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        create_donation_with_details(
            user_state['data']['chat_id'], 
            user_state['data']['message_id'],
            message.from_user,
            user_state['data']['amount'],
            user_state['data'].get('donor_name', ''),
            donor_message
        )

        clear_user_state(message.from_user.id)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        clear_user_state(message.from_user.id)

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id)['state'] == 'collecting_custom_amount')
def collect_custom_amount(message):
    try:
        user_state = get_user_state(message.from_user.id)
        amount_text = message.text.strip()

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        if not amount_text.isdigit():
            bot.edit_message_text("❌ **Error!**\n\nNominal harus berupa angka!\n\nContoh: `15000`\n\nSilakan coba lagi...", user_state['data']['chat_id'], user_state['data']['message_id'], parse_mode='Markdown')
            return

        amount = int(amount_text)

        if amount < 1000:
            bot.edit_message_text("❌ **Error!**\n\nMinimal donasi Rp 1.000\n\nSilakan coba lagi...", user_state['data']['chat_id'], user_state['data']['message_id'], parse_mode='Markdown')
            return

        if amount > 1000000:
            bot.edit_message_text("❌ **Error!**\n\nMaksimal donasi Rp 1.000.000\n\nSilakan coba lagi...", user_state['data']['chat_id'], user_state['data']['message_id'], parse_mode='Markdown')
            return

        user_state['data']['amount'] = amount
        set_user_state(message.from_user.id, 'collecting_name', user_state['data'])

        name_markup = types.InlineKeyboardMarkup()
        btn_skip_name = types.InlineKeyboardButton("⏭️ Skip (Anonim)", callback_data=f"skip_name_{amount}")
        btn_cancel = types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_collection")
        name_markup.add(btn_skip_name)
        name_markup.add(btn_cancel)

        name_text = f"""💝 **Donasi Rp {amount:,}**

📝 **Langkah 1/2: Masukkan Nama Anda**

Ketik nama yang ingin ditampilkan di donasi.
Contoh: `John Doe`

💡 Atau klik "Skip" jika ingin anonim.""".replace(',', '.')

        bot.edit_message_text(name_text, user_state['data']['chat_id'], user_state['data']['message_id'], parse_mode='Markdown', reply_markup=name_markup)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        clear_user_state(message.from_user.id)

# Callback Query Handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith(('donate_', 'custom_donate')))
def handle_donation_amount(call):
    try:
        if is_banned(call.from_user.id):
            bot.answer_callback_query(call.id, "🚫 Anda telah di-blacklist!", show_alert=True)
            return

        if has_pending_donation(call.from_user.id):
            bot.answer_callback_query(call.id, "⚠️ Anda masih memiliki donasi yang belum selesai!", show_alert=True)
            return

        if call.data == 'custom_donate':
            bot.answer_callback_query(call.id, "🔢 Custom Amount")
            set_user_state(call.from_user.id, 'collecting_custom_amount', {'message_id': call.message.message_id, 'chat_id': call.message.chat.id})

            custom_markup = types.InlineKeyboardMarkup()
            btn_cancel = types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_collection")
            custom_markup.add(btn_cancel)

            custom_text = """🔢 **Custom Amount Donation**

💰 **Masukkan nominal donasi (dalam Rupiah):**

Contoh: `15000`, `25000`, `75000`

💡 **Minimum:** Rp 1.000
💡 **Maximum:** Rp 1.000.000

Ketik nominal yang diinginkan..."""

            bot.edit_message_text(custom_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=custom_markup)
            return

        amount = int(call.data.split('_')[1])
        bot.answer_callback_query(call.id, "💝 Siapkan donasi...")

        set_user_state(call.from_user.id, 'collecting_name', {'amount': amount, 'message_id': call.message.message_id, 'chat_id': call.message.chat.id})

        name_markup = types.InlineKeyboardMarkup()
        btn_skip_name = types.InlineKeyboardButton("⏭️ Skip (Anonim)", callback_data=f"skip_name_{amount}")
        btn_cancel = types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_collection")
        name_markup.add(btn_skip_name)
        name_markup.add(btn_cancel)

        name_text = f"""💝 **Donasi Rp {amount:,}**

📝 **Langkah 1/2: Masukkan Nama Anda**

Ketik nama yang ingin ditampilkan di donasi.
Contoh: `John Doe`

💡 Atau klik "Skip" jika ingin anonim.""".replace(',', '.')

        bot.edit_message_text(name_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=name_markup)

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def handle_confirm(call):
    handle_donation_confirmation(bot, call, donation_qris_code)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def handle_cancel_callback(call):
    try:
        donation_id = int(call.data.split('_')[1])
        bot.answer_callback_query(call.id, "❌ Donasi dibatalkan")

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE donations SET status = ? WHERE id = ?', ('cancelled', donation_id))
        conn.commit()
        conn.close()

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"Failed to delete cancelled donation message: {e}")

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('admin_approve_', 'admin_reject_', 'admin_ban_', 'admin_unban_')))
def handle_admin_callback(call):
    handle_admin_verification(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('skip_name_'))
def handle_skip_name_callback(call):
    try:
        amount = int(call.data.split('_')[2])
        user_state = get_user_state(call.from_user.id)

        user_state['data']['donor_name'] = ""
        set_user_state(call.from_user.id, 'collecting_message', user_state['data'])

        bot.answer_callback_query(call.id, "⏭️ Lanjut ke pesan...")

        message_markup = types.InlineKeyboardMarkup()
        btn_skip_message = types.InlineKeyboardButton("⏭️ Skip Pesan", callback_data=f"skip_message_{amount}")
        btn_cancel = types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_collection")
        message_markup.add(btn_skip_message)
        message_markup.add(btn_cancel)

        message_text = f"""💝 **Donasi Rp {amount:,}**
👤 **Nama:** Anonim

📝 **Langkah 2/2: Masukkan Pesan (Opsional)**

Ketik pesan yang ingin ditampilkan.
Contoh: `Terima kasih atas karya yang luar biasa!`

💡 Atau klik "Skip" jika tidak ingin menambah pesan.""".replace(',', '.')

        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=message_markup)

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('skip_message_'))
def handle_skip_message_callback(call):
    try:
        amount = int(call.data.split('_')[2])
        user_state = get_user_state(call.from_user.id)

        bot.answer_callback_query(call.id, "🔄 Membuat QRIS...")

        create_donation_with_details(
            call.message.chat.id, 
            call.message.message_id,
            call.from_user,
            amount,
            user_state['data'].get('donor_name', ''),
            ""
        )

        clear_user_state(call.from_user.id)

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_collection')
def handle_cancel_collection_callback(call):
    try:
        bot.answer_callback_query(call.id, "❌ Dibatalkan")
        
        # Clear user state safely
        clear_user_state(call.from_user.id)
        
        # Send cancellation confirmation
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
            print(f"Failed to edit cancel message: {edit_error}")
            # Fallback: delete and send new message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                cancel_msg = bot.send_message(call.message.chat.id, cancel_text, parse_mode='Markdown')
                auto_delete_message(bot, call.message.chat.id, cancel_msg.message_id, 30)
            except Exception as fallback_error:
                print(f"Fallback cancel handling failed: {fallback_error}")

    except Exception as e:
        print(f"Cancel collection error: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Dibatalkan")
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data == 'start_donation')
def handle_start_donation_callback(call):
    bot.answer_callback_query(call.id)
    start_donation_command(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'back_donate')  
def handle_back_donate_callback(call):
    bot.answer_callback_query(call.id)
    start_donation_command(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_setup')
def handle_admin_setup_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Akses ditolak!")
        return
    bot.answer_callback_query(call.id)
    setup_qris_command(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def handle_admin_stats_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Akses ditolak!")
        return

    bot.answer_callback_query(call.id, "📊 Loading stats...")
    stats_command(bot, call.message)

def create_donation_with_details(chat_id, message_id, user, amount, donor_name="", donor_message=""):
    """Create donation with all details"""
    try:
        global donation_qris_code
        if not donation_qris_code:
            donation_qris_code = load_donation_qris()

        if not donation_qris_code:
            bot.edit_message_text("❌ Sistem donasi belum di-setup.", chat_id, message_id)
            return

        # Generate QRIS donasi
        qris_data = generate_qris(donation_qris_code, amount)

        if not qris_data or 'QR' not in qris_data:
            bot.edit_message_text("❌ Gagal membuat QRIS donasi.", chat_id, message_id)
            return

        qr_code = qris_data['QR']

        # Generate random ID dan pilih item donasi random
        random_id = generate_random_id()
        donation_item = get_random_donation_item()

        # Simpan ke database
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO donations (random_id, qris_id, amount, donor_name, message, donation_item, status, telegram_user_id, telegram_username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (random_id, qr_code[:20], amount, donor_name, donor_message, donation_item, 'pending', user.id, user.username or ""))
        donation_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Buat sticker donasi
        sticker_img = create_donation_sticker(qr_code, amount, donor_name, donor_message)

        # Create button
        markup = types.InlineKeyboardMarkup()
        btn_confirm = types.InlineKeyboardButton(f"✅ Sudah Bayar", callback_data=f"confirm_{donation_id}")
        btn_cancel = types.InlineKeyboardButton(f"❌ Cancel", callback_data=f"cancel_{donation_id}")
        markup.add(btn_confirm, btn_cancel)

        display_name = donor_name if donor_name else (user.first_name or "Seseorang")
        caption = f"""**DONASI - aldo soft**

{display_name} memberi {donation_item} dengan nominal Rp {amount:,}  
🆔 {random_id}"""

        if donor_message:
            caption += f"\n💬 {donor_message}"

        caption += f"""

**Cara Donasi:**
1. Scan QR Code dengan e-wallet
2. Selesaikan pembayaran
3. Klik tombol "Sudah Bayar" di bawah

Terima kasih atas dukungannya! 💝""".replace(',', '.')

        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass

        photo_msg = bot.send_photo(chat_id, sticker_img, caption=caption, parse_mode='Markdown', reply_markup=markup)
        auto_delete_message(bot, chat_id, photo_msg.message_id, AUTO_DELETE_DONATION)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id, message_id)
        print(f"Create donation error: {e}")

def create_thank_you_image(donor_name, amount, donation_item):
    """Create thank you image after donation approval"""
    try:
        # Create thank you image
        width, height = 650, 400
        bg = Image.new('RGB', (width, height), '#f8f9fa')
        draw = ImageDraw.Draw(bg)

        # Load fonts
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            normal_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()

        # Draw gradient background
        for y in range(height):
            r = int(248 + (52 - 248) * y / height)
            g = int(249 + (152 - 249) * y / height)
            b = int(250 + (219 - 250) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Thank you title
        title_text = "🙏 TERIMA KASIH! 🙏"
        draw.text((width//2, 60), title_text, font=title_font, fill="#2d3436", anchor="mm")

        # Donor info
        donor_display = donor_name if donor_name else "Donatur Anonymous"
        donor_text = f"Dari: {donor_display}"
        draw.text((width//2, 120), donor_text, font=subtitle_font, fill="#636e72", anchor="mm")

        # Amount
        amount_text = f"Nominal: Rp {amount:,}".replace(',', '.')
        draw.text((width//2, 160), amount_text, font=subtitle_font, fill="#00b894", anchor="mm")

        # Item
        item_text = f"Item: {donation_item}"
        draw.text((width//2, 200), item_text, font=normal_font, fill="#74b9ff", anchor="mm")

        # Thank you message
        thanks_text = "Donasi Anda sangat berarti untuk pengembangan project ini!"
        draw.text((width//2, 260), thanks_text, font=normal_font, fill="#2d3436", anchor="mm")

        # Signature
        signature_text = "- aldo soft -"
        draw.text((width//2, 320), signature_text, font=normal_font, fill="#636e72", anchor="mm")

        # Heart decoration
        draw.text((width//2, 360), "💝 💝 💝", font=normal_font, fill="#e17055", anchor="mm")

        # Convert to bytes
        img_bytes = BytesIO()
        bg.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes

    except Exception as e:
        print(f"Thank you image creation error: {e}")
        return None

def start_bot():
    """Start the bot"""
    print("🤖 Starting Donation Bot...")
    init_db()
    print("✅ Database initialized")

    # Load existing QRIS if available
    global donation_qris_code
    donation_qris_code = load_donation_qris()
    if donation_qris_code:
        print("✅ Donation QRIS loaded")

    try:
        bot.remove_webhook()
    except:
        pass

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🚀 Donation Bot is running... (attempt {attempt + 1})")
            bot.infinity_polling(none_stop=True, timeout=10, long_polling_timeout=5)
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt < max_retries - 1:
                print("🔄 Retrying in 3 seconds...")
                time.sleep(3)
            else:
                sys.exit(1)

if __name__ == '__main__':
    start_bot()
