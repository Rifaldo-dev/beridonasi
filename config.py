
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 1704985763))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
NOTIFICATION_CHANNEL = os.getenv("NOTIFICATION_CHANNEL", "@beridonasi")

# Database Configuration
DATABASE_NAME = os.getenv("DATABASE_NAME", "donation_bot.db")

# Auto-delete Configuration
AUTO_DELETE_DONATION = int(os.getenv("AUTO_DELETE_DONATION", 600))
AUTO_DELETE_WELCOME = int(os.getenv("AUTO_DELETE_WELCOME", 120))
AUTO_DELETE_SUCCESS = int(os.getenv("AUTO_DELETE_SUCCESS", 300))

# Donation Items
DONATION_ITEMS = {
    "makanan": [
        "Pizza", "Burger", "Mie Ayam", "Nasi Goreng", "Seblak",
        "Sate Taichan", "Ayam Geprek", "Nasi Padang", "Bakso Beranak", "Indomie Telur Kornet",
        "Roti Bakar Coklat Keju", "Telur Ceplok", "Kebab Kilat", "Lontong Sayur", "Pecel Lele",
        "Telur Dadar Setengah Matang", "Sarden Kalengan", "Tahu Gejrot", "Sereal Anak Kos"
    ],
    "minuman": [
        "Es Teh Manis", "Kopi Sachet", "Jus Mangga", "Teh Tarik", "Air Rebusan Jahe",
        "Susu Kedelai", "Susu Kambing", "Es Degan", "Sirup Marjan", "Cendol Duren",
        "Susu Milo Dingin", "Air Galon Tetangga", "Teh Pucuk Bekas Seminar", "Sari Kacang Ijo", "Air Embun Pagi",
        "Nutrisari Tumpah", "Kopi Tubruk Panas", "Minuman Warung Sebelah"
    ],
    "cemilan": [
        "Basreng", "Makaroni Pedas", "Cimol", "Chiki Balls", "Kacang Telur",
        "Keripik Singkong", "Permen Davos", "Wafer Astor", "Roti Sobek", "Cireng Isi",
        "Cilok Saos Tomat", "Tahu Bulat", "Permen Karet 100 Rupiah", "Chitato Rasa Rindu", "Kuaci Tumpah",
        "Chiki Bekas Ultah", "Donat Kentang", "Snack Spongebob", "Popcorn Film Bajakan"
    ],
    "kebutuhan": [
        "Celana Dalam", "Minyak Kayu Putih", "Pulsa 5 Ribu", "Tisu Magic", "Minyak Goreng",
        "Sampo Sachet", "Sikat Gigi", "Sabun Cuci Piring", "Parfum Refill", "Kaos Oblong",
        "Uang Laundry", "Plastik Kresek", "Powerbank Pinjaman", "Paku dan Martil", "Kabel USB Bekas",
        "Stiker Lucu", "Senter HP", "Obeng Multifungsi", "Bantal Guling", "Buku Catatan Niat"
    ],
    "hiburan": [
        "Langganan Netflix", "Voucher Game", "Top Up ML", "Nonton Konser", "Langganan Spotify",
        "Buku Komik", "Majalah Remaja", "Rental PS", "Karaoke", "Mainan Happy Meal",
        "TikTok Premium (ngarep)", "Voucher Warnet", "Game PS2 Bajakan", "Streaming Drama Korea", "Kartu UNO",
        "Langganan VPN Gratisan", "Pulsa Buat Gebetan", "Sticker Line Lucu", "TikTok Ads Buat Pamer", "Bubble Wrap Stres"
    ]
}
