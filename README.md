# Beri Donasi

Bot Telegram untuk sistem donasi dengan pembayaran QRIS. Terinspirasi dari Saweria dan Trakteer.

[Demo Bot](https://t.me/beridonasibot)

## Fitur

- Donasi QRIS Universal - Semua e-wallet (GoPay, DANA, OVO, LinkAja, dll.)
- Nominal preset & input custom
- Verifikasi manual oleh admin
- Auto post ke channel
- Statistik donasi real-time
- Anti-spam & blacklist user
- 80+ item donasi siap pakai
- Item custom dan stiker bermerek

## Instalasi

### Prasyarat
- Python 3.8+
- Telegram Bot Token dari [@BotFather](https://t.me/BotFather)
- QRIS code
- Telegram Channel (opsional)

### Setup

1. Clone repository
   ```bash
   git clone https://github.com/Rifaldo-dev/beridonasi
   cd beridonasi
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Buat file `.env`
   ```bash
   cp .env.example .env
   ```

4. Isi konfigurasi di `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token
   CHANNEL_ID=your_channel_id
   ADMIN_IDS=123456789,987654321
   QRIS_CODE=your_qris_code
   ```

5. Jalankan bot
   ```bash
   python main.py
   ```

## Penggunaan

Akses bot: [Beri Donasi Bot](https://t.me/beridonasibot)

Perintah utama: `/start`, `/donasi`, `/stats`, `/admin`

## Lisensi

MIT License
