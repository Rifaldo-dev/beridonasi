import random
import string
import threading
import time
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from database import get_all_donation_items
from logger_config import get_logger
from services import QRISService

logger = get_logger(__name__)

def generate_random_id():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(chars, k=8))

def get_random_donation_item():
    try:
        all_items = get_all_donation_items()
        return random.choice(all_items) if all_items else "🎁 Item Donasi"
    except Exception as e:
        logger.error(f"Error getting random item: {e}")
        return "🎁 Item Donasi"

def is_admin(user_id):
    from config import ADMIN_USER_ID
    return user_id == ADMIN_USER_ID

def generate_qris(qris_code, amount):
    try:
        service = QRISService()
        return service.generate_qris(qris_code, amount)
    except Exception as e:
        logger.error(f"Generate QRIS error: {e}")
        return None

def _load_fonts(sizes):
    fonts = {}
    for name, size in sizes.items():
        try:
            fonts[name] = ImageFont.truetype("arial.ttf", size)
        except:
            fonts[name] = ImageFont.load_default()
    return fonts

def _draw_text_centered(draw, width, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, y), text, fill=fill, font=font)

def _draw_rounded_box(draw, width, y, height, bg_color, text_color, title, content, title_font, content_font, bg_image=None):
    if bg_image is None:
        bg = Image.new('RGBA', (width-30, height), bg_color)
        bg_draw = ImageDraw.Draw(bg)
        bg_draw.rounded_rectangle([0, 0, width-30, height], radius=15, outline=(255, 182, 193), width=2)
        bg_image.paste(bg, (15, y), bg)
    
    draw.text((width//2, y+25), title, font=title_font, fill=text_color, anchor="mm")
    draw.text((width//2, y+50), content[:30], font=content_font, fill="#d63384", anchor="mm")

def create_donation_sticker(qr_data, amount, donor_name="", message=""):
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=18,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

        width, height = 650, 900
        bg = Image.new('RGB', (width, height), '#ffffff')
        draw = ImageDraw.Draw(bg)

        for i in range(height):
            progress = i / height
            if progress < 0.3:
                t = progress / 0.3
                r = int(255 - t * 10)
                g = int(248 - t * 20)  
                b = int(245 - t * 30)
            elif progress < 0.7:
                t = (progress - 0.3) / 0.4
                r = int(245 - t * 5)
                g = int(228 - t * 8)
                b = int(215 - t * 15)
            else:
                t = (progress - 0.7) / 0.3
                r = int(240 - t * 10)
                g = int(220 - t * 10)
                b = int(200 - t * 10)
            draw.line([(0, i), (width, i)], fill=(r, g, b))

        border_color = (200, 150, 100)
        for t in range(3):
            draw.rectangle([t, t, width-1-t, height-1-t], outline=border_color, width=1)

        sizes = {
            'header': 52, 'brand': 42, 'title': 48, 'subtitle': 32,
            'amount': 72, 'medium': 24, 'small': 20, 'tiny': 18
        }
        fonts = _load_fonts(sizes)

        header_height = 120
        header_bg = Image.new('RGBA', (width-20, header_height), (255, 107, 107, 240))
        draw_header = ImageDraw.Draw(header_bg)
        draw_header.rounded_rectangle([0, 0, width-20, header_height], radius=20, outline=(200, 80, 80), width=2)
        bg.paste(header_bg, (10, 15), header_bg)

        draw.text((width//2, 50), "BERI DONASI", font=fonts['header'], fill="#ffffff", anchor="mm")
        draw.text((width//2, 85), "Dukung Karya Kami", font=fonts['medium'], fill="#ffffff", anchor="mm")

        current_y = 150
        if donor_name:
            donor_height = 80
            donor_bg = Image.new('RGBA', (width-30, donor_height), (255, 255, 255, 250))
            draw_donor = ImageDraw.Draw(donor_bg)
            draw_donor.rounded_rectangle([0, 0, width-30, donor_height], radius=15, outline=(255, 182, 193), width=2)
            bg.paste(donor_bg, (15, current_y), donor_bg)
            draw.text((width//2, current_y+25), "DONATUR", font=fonts['tiny'], fill="#666666", anchor="mm")
            draw.text((width//2, current_y+50), donor_name[:30], font=fonts['subtitle'], fill="#d63384", anchor="mm")
            current_y += 95

        if message:
            message_height = max(60, min(120, len(message) // 20 * 20 + 60))
            message_bg = Image.new('RGBA', (width-30, message_height), (248, 249, 250, 250))
            draw_message = ImageDraw.Draw(message_bg)
            draw_message.rounded_rectangle([0, 0, width-30, message_height], radius=12, outline=(220, 220, 220), width=1)
            bg.paste(message_bg, (15, current_y), message_bg)
            draw.text((width//2, current_y+20), "PESAN", font=fonts['tiny'], fill="#666666", anchor="mm")
            
            words = message[:100].split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= 40:
                    current_line += (" " + word) if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            for i, line in enumerate(lines[:3]):
                draw.text((width//2, current_y+45+i*25), line, font=fonts['small'], fill="#495057", anchor="mm")

            current_y += message_height + 15

        qr_size = 320
        qr_img_hd = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        qr_x = (width - qr_size) // 2
        qr_y = current_y + 20

        shadow_offset = 5
        shadow = Image.new('RGBA', (qr_size + shadow_offset*2, qr_size + shadow_offset*2), (0, 0, 0, 50))
        bg.paste(shadow, (qr_x-shadow_offset, qr_y-shadow_offset), shadow)

        frame_color = (255, 107, 107)
        draw.rounded_rectangle([qr_x-15, qr_y-15, qr_x+qr_size+15, qr_y+qr_size+15], radius=20, outline=frame_color, width=4)
        draw.rounded_rectangle([qr_x-10, qr_y-10, qr_x+qr_size+10, qr_y+qr_size+10], radius=15, fill="white", outline=(240, 240, 240), width=2)
        bg.paste(qr_img_hd, (qr_x, qr_y), qr_img_hd)

        amount_y = qr_y + qr_size + 30
        amount_text = f"Rp {amount:,}".replace(',', '.')
        amount_height = 80
        amount_bg = Image.new('RGBA', (width-20, amount_height), (220, 53, 69, 255))
        bg.paste(amount_bg, (10, amount_y-10), amount_bg)
        draw.rounded_rectangle([10, amount_y-10, width-10, amount_y+70], radius=15, outline=(180, 40, 50), width=3)
        draw.text((width//2, amount_y+30), amount_text, font=fonts['amount'], fill="#FFFFFF", anchor="mm")

        instruction_y = amount_y + 100
        instructions = [
            ("Scan QR Code dengan aplikasi e-wallet", fonts['small'], "#495057"),
            ("DANA • OVO • GoPay • ShopeePay • LinkAja", fonts['tiny'], "#6c757d"),
        ]
        for i, (text, font, color) in enumerate(instructions):
            y_pos = instruction_y + i * 25
            draw.text((width//2, y_pos), text, font=font, fill=color, anchor="mm")

        footer_y = instruction_y + 80
        draw.line([(30, footer_y), (width-30, footer_y)], fill=(255, 182, 193), width=2)
        footer_items = [
            ("Terima kasih atas dukungannya!", fonts['small'], "#d63384"),
            ("aldo soft", fonts['medium'], "#495057")
        ]
        for i, (text, font, color) in enumerate(footer_items):
            y_pos = footer_y + 20 + i * 25
            draw.text((width//2, y_pos), text, font=font, fill=color, anchor="mm")

        bio = BytesIO()
        bg.save(bio, 'PNG', quality=100, optimize=False, dpi=(600, 600))
        bio.seek(0)
        return bio

    except Exception as e:
        print(f"Sticker creation error: {e}")
        return None

def auto_delete_message(bot, chat_id, message_id, delay_seconds=300):
    def delete_after_delay():
        time.sleep(delay_seconds)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Auto-delete failed: {e}")

    thread = threading.Thread(target=delete_after_delay)
    thread.daemon = True
    thread.start()
