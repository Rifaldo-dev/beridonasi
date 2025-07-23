import sqlite3
import telebot
from telebot import types
from config import *
from database import *
from utils import *

def welcome_command(bot, message):
    """Welcome command handler"""
    try:
        user_name = message.from_user.first_name or "Pengguna"

        welcome_text = f"""
👋 **Selamat datang {user_name}!**

🤖 **Donation Bot - aldo soft**
Bot untuk sistem donasi dengan payment QRIS

✨ **Fitur Utama:**
• 💝 Donasi mudah via QRIS  
• 🎁 Multiple pilihan nominal
• 📝 Custom message & nama
• ⚡ Verifikasi admin real-time
• 📊 Notifikasi ke channel

🚀 **Mulai Donasi:**"""

        markup = types.InlineKeyboardMarkup()
        btn_donate = types.InlineKeyboardButton("💝 Mulai Donasi", callback_data="start_donation")

        if is_admin(message.from_user.id):
            btn_setup = types.InlineKeyboardButton("⚙️ Setup QRIS", callback_data="admin_setup")
            btn_stats = types.InlineKeyboardButton("📊 Statistik", callback_data="admin_stats")
            markup.add(btn_donate)
            markup.add(btn_setup, btn_stats)
        else:
            markup.add(btn_donate)

        welcome_msg = bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)
        auto_delete_message(bot, message.chat.id, welcome_msg.message_id, 120)
        auto_delete_message(bot, message.chat.id, message.message_id, 30)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def setup_qris_command(bot, message):
    """Setup QRIS command handler"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ **HANYA ADMIN YANG DAPAT SETUP QRIS**\n\nCommand `/setupqris` hanya dapat digunakan oleh admin.", parse_mode='Markdown')
            return

        setup_text = """🔧 **Setup QRIS Donasi**

📱 **Langkah Setup:**
1. Buka aplikasi e-wallet (Dana/GoPay/OVO/dll)
2. Pilih "Terima Uang" atau "QR Code"
3. Screenshot atau copy QRIS code
4. Kirim QRIS code ke bot ini

⚠️ **Penting:**
• Pastikan QRIS dapat menerima amount dinamis
• QRIS akan digunakan untuk semua donasi
• Hanya admin yang dapat mengubah QRIS

📤 **Kirim QRIS code sekarang:**"""

        setup_msg = bot.reply_to(message, setup_text, parse_mode='Markdown')
        set_user_state(message.from_user.id, 'setup_qris', {'message_id': setup_msg.message_id, 'chat_id': message.chat.id})

        # Delete original command
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

    except Exception as e:
        bot.reply_to(message, f"❌ Setup error: {str(e)}")

def start_donation_command(bot, message):
    """Start donation command"""
    try:
        if is_banned(message.from_user.id):
            bot.reply_to(message, "🚫 **ANDA TELAH DIBLACKLIST**\n\nAnda tidak dapat menggunakan sistem donasi karena telah bermain-main dengan sistem ini.\n\n⚠️ Jangan bermain-main agar tidak di-blacklist!", parse_mode='Markdown')
            return

        if has_pending_donation(message.from_user.id):
            bot.reply_to(message, "⚠️ **DONASI AKTIF DITEMUKAN**\n\nAnda masih memiliki donasi yang belum selesai.\n\nGunakan `/cancel` untuk membatalkan donasi aktif, atau selesaikan donasi yang sedang berjalan.", parse_mode='Markdown')
            return

        donation_qris_code = load_donation_qris()

        if not donation_qris_code:
            error_text = "❌ **SISTEM DONASI BELUM SIAP**\n\nQRIS belum di-setup oleh admin.\n\n"
            if is_admin(message.from_user.id):
                error_text += "🔧 Gunakan `/setupqris` untuk setup QRIS."
            else:
                error_text += "📞 Hubungi admin untuk setup sistem."

            bot.reply_to(message, error_text, parse_mode='Markdown')
            return

        # Inline keyboard untuk pilihan donasi
        markup = types.InlineKeyboardMarkup(row_width=2)

        amounts = [5000, 10000, 25000, 50000, 100000, 200000]
        for i in range(0, len(amounts), 2):
            row = []
            for j in range(2):
                if i + j < len(amounts):
                    amount = amounts[i + j]
                    btn = types.InlineKeyboardButton(f"💝 Rp {amount:,}".replace(',', '.'), 
                                                   callback_data=f"donate_{amount}")
                    row.append(btn)
            markup.row(*row)

        btn_custom = types.InlineKeyboardButton("🔢 Custom Amount", callback_data="custom_donate")
        markup.add(btn_custom)

        welcome_text = f"""💝 **Beri Donasi - aldo soft**

Halo {message.from_user.first_name}! 

Terima kasih ingin mendukung karya kami. Setiap donasi Anda sangat berarti untuk pengembangan project ini.

💰 **Pilih nominal donasi:**

💡 *Tips: Untuk custom amount, pilih tombol di bawah*
⚡ *Proses: Instant dengan QRIS scan*"""

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        donation_msg = bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)
        auto_delete_message(bot, message.chat.id, donation_msg.message_id, 300)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def custom_donation_command(bot, message):
    """Custom donation command handler"""
    try:
        if is_banned(message.from_user.id):
            bot.reply_to(message, "🚫 **ANDA TELAH DIBLACKLIST**\n\nAnda tidak dapat menggunakan sistem donasi.", parse_mode='Markdown')
            return

        if has_pending_donation(message.from_user.id):
            bot.reply_to(message, "⚠️ Anda masih memiliki donasi yang belum selesai!")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, """❌ **Format salah!**

**Penggunaan:**
`/beri <nominal> [nama] [pesan]`

**Contoh:**
• `/beri 15000`
• `/beri 25000 John Doe`
• `/beri 50000 John Doe Terima kasih!`

**Catatan:**
• Minimal Rp 1.000, maksimal Rp 1.000.000
• Nama dan pesan opsional""", parse_mode='Markdown')
            return

        try:
            amount = int(args[1])
        except ValueError:
            bot.reply_to(message, "❌ Nominal harus berupa angka!\nContoh: `/beri 15000`", parse_mode='Markdown')
            return

        if amount < 1000:
            bot.reply_to(message, "❌ Minimal donasi Rp 1.000")
            return

        if amount > 1000000:
            bot.reply_to(message, "❌ Maksimal donasi Rp 1.000.000")
            return

        donor_name = args[2] if len(args) > 2 else ""
        donor_message = " ".join(args[3:]) if len(args) > 3 else ""

        # Create donation directly
        creating_msg = bot.reply_to(message, f"🔄 **Membuat donasi Rp {amount:,}...**\n\n⏳ Mohon tunggu sebentar...".replace(',', '.'), parse_mode='Markdown')

        # Import here to avoid circular import
        from main import create_donation_with_details
        create_donation_with_details(
            creating_msg.chat.id,
            creating_msg.message_id,
            message.from_user,
            amount,
            donor_name,
            donor_message
        )

        # Delete original command
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def stats_command(bot, message):
    """Statistics command handler"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ **HANYA ADMIN YANG DAPAT MELIHAT STATISTIK**\n\nCommand `/stats` hanya dapat digunakan oleh admin.", parse_mode='Markdown')
            return

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Get donation statistics
        cursor.execute('SELECT status, COUNT(*), SUM(amount) FROM donations GROUP BY status')
        stats_data = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) FROM donations')
        total_donations = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(amount) FROM donations WHERE status = "approved"')
        total_approved_amount = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM banned_users')
        total_banned = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM custom_donation_items')
        total_custom_items = cursor.fetchone()[0]

        # Get recent donations
        cursor.execute('''
            SELECT random_id, donor_name, amount, status, timestamp 
            FROM donations 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        recent_donations = cursor.fetchall()

        conn.close()

        stats_text = f"""📊 **STATISTIK DONASI - aldo soft**

📈 **Ringkasan:**
• 🎯 Total Donasi: {total_donations} transaksi
• 💰 Total Approved: Rp {total_approved_amount:,}
• 🚫 User Banned: {total_banned} user
• 🎁 Item Custom: {total_custom_items} item

📋 **Status Donasi:**""".replace(',', '.')

        status_emoji = {
            'pending': '⏳',
            'submitted': '📨', 
            'approved': '✅',
            'rejected': '❌',
            'cancelled': '🚫'
        }

        for status, count, amount in stats_data:
            emoji = status_emoji.get(status, '📄')
            amount_display = f"Rp {amount:,}" if amount else "Rp 0"
            stats_text += f"\n• {emoji} {status.title()}: {count} ({amount_display})"

        stats_text = stats_text.replace(',', '.')

        if recent_donations:
            stats_text += f"\n\n🕐 **Donasi Terbaru:**"
            for random_id, donor_name, amount, status, timestamp in recent_donations:
                donor_display = donor_name if donor_name else "Anonim"
                status_emoji_recent = status_emoji.get(status, '📄')
                stats_text += f"\n• {random_id} - {donor_display} - Rp {amount:,} {status_emoji_recent}"

        stats_text = stats_text.replace(',', '.')
        stats_text += f"\n\n⚡ **Admin Commands:**"
        stats_text += f"\n• `/ban <user_id>` - Ban user"
        stats_text += f"\n• `/unban <user_id>` - Unban user"
        stats_text += f"\n• `/add <item> <harga>` - Tambah item"

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        stats_msg = bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')
        auto_delete_message(bot, message.chat.id, stats_msg.message_id, 180)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")