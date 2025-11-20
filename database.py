import sqlite3
from config import DATABASE_NAME
from logger_config import get_logger

logger = get_logger(__name__)

def _get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS donations')
    cursor.execute('''
        CREATE TABLE donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            random_id TEXT UNIQUE NOT NULL,
            donor_name TEXT DEFAULT '',
            message TEXT DEFAULT '',
            amount INTEGER NOT NULL,
            donation_item TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            qris_id TEXT,
            telegram_user_id INTEGER,
            telegram_username TEXT DEFAULT ''
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            banned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT DEFAULT 'Bermain-main dengan sistem donasi'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_donation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database schema initialized successfully")
    print("✅ Database schema updated successfully")

def get_all_donation_items():
    from config import DONATION_ITEMS
    all_items = []
    for category_items in DONATION_ITEMS.values():
        all_items.extend(category_items)
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT item_name FROM custom_donation_items')
    custom_items = cursor.fetchall()
    conn.close()
    for item in custom_items:
        all_items.append(item[0])
    return all_items

def save_donation_qris(qris_code):
    from services import QRISService
    service = QRISService()
    service.save_qris_code(qris_code)

def load_donation_qris():
    from services import QRISService
    service = QRISService()
    return service.load_qris_code()

def is_banned(user_id):
    from services import UserService
    service = UserService()
    return service.is_banned(user_id)

def has_pending_donation(user_id):
    from services import UserService
    service = UserService()
    return service.has_pending_donation(user_id)

def ban_user(user_id, username="", reason=""):
    from services import UserService
    service = UserService()
    service.ban_user(user_id, username, reason)

def unban_user(user_id):
    from services import UserService
    service = UserService()
    return service.unban_user(user_id)

def add_custom_donation_item(item_name, price, created_by):
    from services import UserService
    service = UserService()
    service.add_custom_item(item_name, price, created_by)

def set_user_state(user_id, state, data=None):
    from models import UserState
    UserState.set(user_id, state, data)

def get_user_state(user_id):
    from models import UserState
    return UserState.get(user_id)

def clear_user_state(user_id):
    from models import UserState
    UserState.clear(user_id)