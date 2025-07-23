import random
import string
import threading
import time
import requests
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from database import get_all_donation_items

def generate_random_id():
    """Generate random ID with letters and numbers only"""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(chars, k=8))

def get_random_donation_item():
    """Get random donation item from all available items"""
    try:
        all_items = get_all_donation_items()
        if all_items:
            return random.choice(all_items)
        else:
            return "🎁 Item Donasi"
    except Exception as e:
        print(f"Error getting random item: {e}")
        return "🎁 Item Donasi"

def is_admin(user_id):
    """Check if user is admin"""
    from config import ADMIN_USER_ID
    return user_id == ADMIN_USER_ID

def generate_qris(base_qris, amount):
    """Generate QRIS with amount"""
    try:
        # Simple QRIS generation - modify the base QRIS with amount
        # This is a simplified implementation
        qris_with_amount = f"{base_qris}|{amount}"
        return {'QR': qris_with_amount}
    except Exception as e:
        print(f"QRIS generation error: {e}")
        return None

def create_donation_sticker(qr_code, amount, donor_name="", donor_message=""):
    """Create donation sticker with QR code"""
    try:
        # Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Create a larger canvas for the sticker
        canvas_width, canvas_height = 650, 900
        canvas = Image.new('RGB', (canvas_width, canvas_height), color='white')

        # Resize and paste QR code
        qr_size = 400
        qr_img = qr_img.resize((qr_size, qr_size))
        qr_x = (canvas_width - qr_size) // 2
        qr_y = 150
        canvas.paste(qr_img, (qr_x, qr_y))

        # Create drawing context
        draw = ImageDraw.Draw(canvas)

        # Try to load font, fallback to default if not available
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Add title
        title = "DONASI - aldo soft"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (canvas_width - title_width) // 2
        draw.text((title_x, 50), title, fill='black', font=title_font)

        # Add amount
        amount_text = f"Rp {amount:,}".replace(',', '.')
        amount_bbox = draw.textbbox((0, 0), amount_text, font=title_font)
        amount_width = amount_bbox[2] - amount_bbox[0]
        amount_x = (canvas_width - amount_width) // 2
        draw.text((amount_x, 600), amount_text, fill='black', font=title_font)

        # Add donor name if provided
        if donor_name:
            name_text = f"Dari: {donor_name}"
            name_bbox = draw.textbbox((0, 0), name_text, font=text_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (canvas_width - name_width) // 2
            draw.text((name_x, 650), name_text, fill='black', font=text_font)

        # Add message if provided
        if donor_message:
            msg_text = f'"{donor_message}"'
            if len(msg_text) > 40:
                msg_text = msg_text[:37] + "..."
            msg_bbox = draw.textbbox((0, 0), msg_text, font=small_font)
            msg_width = msg_bbox[2] - msg_bbox[0]
            msg_x = (canvas_width - msg_width) // 2
            y_pos = 690 if donor_name else 650
            draw.text((msg_x, y_pos), msg_text, fill='gray', font=small_font)

        # Add instructions
        instruction = "Scan QR untuk donasi"
        inst_bbox = draw.textbbox((0, 0), instruction, font=small_font)
        inst_width = inst_bbox[2] - inst_bbox[0]
        inst_x = (canvas_width - inst_width) // 2
        draw.text((inst_x, 750), instruction, fill='gray', font=small_font)

        # Convert to bytes
        img_byte_arr = BytesIO()
        canvas.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr

    except Exception as e:
        print(f"Sticker creation error: {e}")
        return None

def auto_delete_message(bot, chat_id, message_id, delay_seconds=300):
    """Auto-delete message after delay"""
    def delete_after_delay():
        time.sleep(delay_seconds)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Auto-delete failed: {e}")

    thread = threading.Thread(target=delete_after_delay)
    thread.daemon = True
    thread.start()

def generate_qris(qris_code, amount):
    """Generate QRIS using API"""
    try:
        api_url = f"https://api-mininxd.vercel.app/qris?qris={qris_code}&nominal={amount}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data and 'QR' in data and data['QR']:
            qr_data = data['QR']
            if qr_data.startswith('00020101') or qr_data.startswith('00020201'):
                if len(qr_data) > 100 and '5204' in qr_data:
                    return data

        return None
    except Exception as e:
        print(f"Generate QRIS error: {e}")
        return None

def create_donation_sticker(qr_data, amount, donor_name="", message=""):
    """Create premium donation sticker"""
    # Generate QR code with HD settings
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=18,
        border=1,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

    # HD dimensions
    width, height = 650, 900

    # Create premium background
    bg = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(bg)

    # Gradient background
    for i in range(height):
        progress = i / height
        if progress < 0.3:
            t = progress / 0.3
            r = int(255 - t * 10)
            g = int(248 - t * 20)  
            b = int(245 - t * 30)
            color = (r, g, b)
        elif progress < 0.7:
            t = (progress - 0.3) / 0.4
            r = int(245 - t * 5)
            g = int(228 - t * 8)
            b = int(215 - t * 15)
            color = (r, g, b)
        else:
            t = (progress - 0.7) / 0.3
            r = int(240 - t * 10)
            g = int(220 - t * 10)
            b = int(200 - t * 10)
            color = (r, g, b)
        draw.line([(0, i), (width, i)], fill=color)

    # Simple clean border
    border_color = (200, 150, 100)
    for t in range(3):
        draw.rectangle([t, t, width-1-t, height-1-t], outline=border_color, width=1)

    # Load fonts
    try:
        header_font = ImageFont.truetype("arial.ttf", 52)
        brand_font = ImageFont.truetype("arial.ttf", 42)
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 32)
        amount_font = ImageFont.truetype("arial.ttf", 72)
        medium_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 20)
        tiny_font = ImageFont.truetype("arial.ttf", 18)
    except:
        header_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        amount_font = ImageFont.load_default()
        medium_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        tiny_font = ImageFont.load_default()

    # Header section
    header_height = 120
    header_bg = Image.new('RGBA', (width-20, header_height), (255, 107, 107, 240))
    draw_header = ImageDraw.Draw(header_bg)
    draw_header.rounded_rectangle([0, 0, width-20, header_height], radius=20, outline=(200, 80, 80), width=2)
    bg.paste(header_bg, (10, 15), header_bg)

    # Header text
    draw.text((width//2, 50), "BERI DONASI", font=header_font, fill="#ffffff", anchor="mm")
    draw.text((width//2, 85), "Dukung Karya Kami", font=medium_font, fill="#ffffff", anchor="mm")

    # Donor info section
    current_y = 150
    if donor_name:
        donor_height = 80
        donor_bg = Image.new('RGBA', (width-30, donor_height), (255, 255, 255, 250))
        draw_donor = ImageDraw.Draw(donor_bg)
        draw_donor.rounded_rectangle([0, 0, width-30, donor_height], radius=15, outline=(255, 182, 193), width=2)
        bg.paste(donor_bg, (15, current_y), donor_bg)
        draw.text((width//2, current_y+25), "DONATUR", font=tiny_font, fill="#666666", anchor="mm")
        draw.text((width//2, current_y+50), donor_name[:30], font=subtitle_font, fill="#d63384", anchor="mm")
        current_y += 95

    # Message section
    if message:
        message_height = max(60, min(120, len(message) // 20 * 20 + 60))
        message_bg = Image.new('RGBA', (width-30, message_height), (248, 249, 250, 250))
        draw_message = ImageDraw.Draw(message_bg)
        draw_message.rounded_rectangle([0, 0, width-30, message_height], radius=12, outline=(220, 220, 220), width=1)
        bg.paste(message_bg, (15, current_y), message_bg)
        draw.text((width//2, current_y+20), "PESAN", font=tiny_font, fill="#666666", anchor="mm")
        
        # Split message into lines
        words = message.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 35:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines[:3]):  # Max 3 lines
            draw.text((width//2, current_y+45+i*18), line, font=normal_font, fill="#495057", anchor="mm")
        current_y += message_height + 15

    # QR Code
    qr_y = current_y + 20
    qr_size = 220
    qr_x = (width - qr_size) // 2
    qr_bg = Image.new('RGB', (qr_size + 20, qr_size + 20), '#ffffff')
    qr_draw = ImageDraw.Draw(qr_bg)
    qr_draw.rectangle([0, 0, qr_size + 20, qr_size + 20], outline="#ddd", width=2)
    bg.paste(qr_bg, (qr_x - 10, qr_y - 10))
    
    qr_img = qr_img.resize((qr_size, qr_size))
    bg.paste(qr_img, (qr_x, qr_y))

    # Footer
    footer_y = qr_y + qr_size + 30
    draw.text((width//2, footer_y), "Scan QR dengan e-wallet favorit Anda", font=normal_font, fill="#6c757d", anchor="mm")
    draw.text((width//2, footer_y + 25), "Dana • GoPay • OVO • ShopeePay • LinkAja", font=tiny_font, fill="#adb5bd", anchor="mm")
    
    # Bottom signature
    draw.text((width//2, height - 40), "- aldo soft -", font=normal_font, fill="#6c757d", anchor="mm")
    
    # Convert to bytes
    img_bytes = BytesIO()
    bg.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes="mm")

        # Wrap message text
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
            draw.text((width//2, current_y+45+i*25), line, font=small_font, fill="#495057", anchor="mm")

        current_y += message_height + 15

    # QR Code section
    qr_size = 320
    qr_img_hd = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    qr_x = (width - qr_size) // 2
    qr_y = current_y + 20

    # QR shadow
    shadow_offset = 5
    shadow = Image.new('RGBA', (qr_size + shadow_offset*2, qr_size + shadow_offset*2), (0, 0, 0, 50))
    bg.paste(shadow, (qr_x-shadow_offset, qr_y-shadow_offset), shadow)

    # QR frame
    frame_color = (255, 107, 107)
    draw.rounded_rectangle([qr_x-15, qr_y-15, qr_x+qr_size+15, qr_y+qr_size+15], radius=20, outline=frame_color, width=4)
    draw.rounded_rectangle([qr_x-10, qr_y-10, qr_x+qr_size+10, qr_y+qr_size+10], radius=15, fill="white", outline=(240, 240, 240), width=2)
    bg.paste(qr_img_hd, (qr_x, qr_y), qr_img_hd)

    # Amount section
    amount_y = qr_y + qr_size + 30
    amount_text = f"Rp {amount:,}".replace(',', '.')
    amount_height = 80

    amount_bg = Image.new('RGBA', (width-20, amount_height), (220, 53, 69, 255))
    bg.paste(amount_bg, (10, amount_y-10), amount_bg)
    draw.rounded_rectangle([10, amount_y-10, width-10, amount_y+70], radius=15, outline=(180, 40, 50), width=3)
    draw.text((width//2, amount_y+30), amount_text, font=amount_font, fill="#FFFFFF", anchor="mm")

    # Payment instructions
    instruction_y = amount_y + 100
    instructions = [
        ("Scan QR Code dengan aplikasi e-wallet", small_font, "#495057"),
        ("DANA • OVO • GoPay • ShopeePay • LinkAja", tiny_font, "#6c757d"),
    ]

    for i, (text, font, color) in enumerate(instructions):
        y_pos = instruction_y + i * 25
        draw.text((width//2, y_pos), text, font=font, fill=color, anchor="mm")

    # Footer
    footer_y = instruction_y + 80
    draw.line([(30, footer_y), (width-30, footer_y)], fill=(255, 182, 193), width=2)

    footer_items = [
        ("Terima kasih atas dukungannya!", small_font, "#d63384"),
        ("aldo soft", medium_font, "#495057")
    ]

    for i, (text, font, color) in enumerate(footer_items):
        y_pos = footer_y + 20 + i * 25
        draw.text((width//2, y_pos), text=text, font=font, fill=color, anchor="mm")

    # Save with HD quality
    bio = BytesIO()
    bg.save(bio, 'PNG', quality=100, optimize=False, dpi=(600, 600))
    bio.seek(0)
    return bio