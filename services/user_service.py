import sqlite3
from config import DATABASE_NAME
from logger_config import get_logger
from exceptions import BanException, AdminException

logger = get_logger(__name__)

class UserService:
    def __init__(self):
        self.db_name = DATABASE_NAME

    def _get_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def is_banned(self, user_id):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM banned_users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking ban status: {e}")
            return False

    def has_pending_donation(self, user_id):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM donations WHERE telegram_user_id = ? AND status IN ("pending", "submitted")', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking pending donation: {e}")
            return False

    def ban_user(self, user_id, username="", reason=""):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO banned_users (user_id, username, reason)
                VALUES (?, ?, ?)
            ''', (user_id, username, reason))
            conn.commit()
            conn.close()
            logger.warning(f"User {user_id} (@{username}) banned. Reason: {reason}")
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            raise

    def unban_user(self, user_id):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            if affected > 0:
                logger.warning(f"User {user_id} unbanned")
            return affected > 0
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            raise

    def get_banned_users(self):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, banned_at, reason FROM banned_users ORDER BY banned_at DESC')
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching banned users: {e}")
            return []

    def add_custom_item(self, item_name, price, created_by):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO custom_donation_items (item_name, price, created_by)
                VALUES (?, ?, ?)
            ''', (item_name, price, created_by))
            conn.commit()
            conn.close()
            logger.info(f"Custom item added: {item_name} (Rp {price:,}) by {created_by}")
        except Exception as e:
            logger.error(f"Error adding custom item: {e}")
            raise

    def get_custom_items(self):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT item_name, price, created_at, created_by FROM custom_donation_items ORDER BY created_at DESC')
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching custom items: {e}")
            return []
