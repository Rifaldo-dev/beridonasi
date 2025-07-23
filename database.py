Refactored clear_user_state function for safer user state clearing with error handling.
```

```python
import sqlite3
from config import DATABASE_NAME

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Drop and recreate donations table
    cursor.execute('DROP TABLE IF EXISTS donations')

    # Create donations table
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

    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Banned users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            banned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT DEFAULT 'Bermain-main dengan sistem donasi'
        )
    ''')

    # Custom donation items table
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
    print("✅ Database schema updated successfully")

def save_donation_qris(qris_code):
    """Save QRIS code to database"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('donation_qris', qris_code))
    conn.commit()
    conn.close()

def load_donation_qris():
    """Load QRIS code from database"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('donation_qris',))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def is_banned(user_id):
    """Check if user is banned"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM banned_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def has_pending_donation(user_id):
    """Check if user has pending donation"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM donations WHERE telegram_user_id = ? AND status IN ("pending", "submitted")', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def ban_user(user_id, username="", reason="Bermain-main dengan sistem donasi"):
    """Ban a user"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO banned_users (user_id, username, reason)
        VALUES (?, ?, ?)
    ''', (user_id, username, reason))
    conn.commit()
    conn.close()

def unban_user(user_id):
    """Unban a user"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def add_custom_donation_item(item_name, price, created_by):
    """Add custom donation item"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO custom_donation_items (item_name, price, created_by)
        VALUES (?, ?, ?)
    ''', (item_name, price, created_by))
    conn.commit()
    conn.close()

def get_all_donation_items():
    """Get all donation items including custom ones"""
    from config import DONATION_ITEMS

    # Get default items
    all_items = []
    for category_items in DONATION_ITEMS.values():
        all_items.extend(category_items)

    # Get custom items
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT item_name FROM custom_donation_items')
    custom_items = cursor.fetchall()
    conn.close()

    for item in custom_items:
        all_items.append(item[0])

    return all_items

# User state management (in-memory)
user_states = {}

def set_user_state(user_id, state, data=None):
    """Set user state"""
    user_states[user_id] = {'state': state, 'data': data or {}}

def get_user_state(user_id):
    """Get user state"""
    return user_states.get(user_id, {'state': None, 'data': {}})

def clear_user_state(user_id):
    """Clear user state safely"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_states WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        print(f"✅ User state cleared for user {user_id}")
    except Exception as e:
        print(f"❌ Error clearing user state for {user_id}: {e}")
        # Don't raise the error, just log it