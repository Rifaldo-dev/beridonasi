import sqlite3
from config import DATABASE_NAME
from logger_config import get_logger
from exceptions import InvalidAmountException, DatabaseException

logger = get_logger(__name__)

class DonationService:
    def __init__(self):
        self.db_name = DATABASE_NAME
        self.min_amount = 1000
        self.max_amount = 1000000

    def _get_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def validate_amount(self, amount):
        if not isinstance(amount, int) or amount < self.min_amount or amount > self.max_amount:
            raise InvalidAmountException(f"Amount must be between Rp {self.min_amount:,} - Rp {self.max_amount:,}")
        return True

    def create_donation(self, random_id, qris_id, amount, donor_name, message, donation_item, user_id, username):
        try:
            self.validate_amount(amount)
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO donations (random_id, qris_id, amount, donor_name, message, donation_item, status, telegram_user_id, telegram_username)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (random_id, qris_id, amount, donor_name, message, donation_item, 'pending', user_id, username or ""))
            donation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Donation created - ID: {donation_id}, User: {user_id}, Amount: Rp {amount:,}")
            return donation_id
        except Exception as e:
            logger.error(f"Error creating donation: {e}")
            raise

    def get_donation(self, donation_id):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching donation: {e}")
            return None

    def update_donation_status(self, donation_id, status):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE donations SET status = ? WHERE id = ?', (status, donation_id))
            conn.commit()
            conn.close()
            logger.info(f"Donation {donation_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error updating donation status: {e}")
            raise

    def get_user_active_donation(self, user_id):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, random_id, amount FROM donations WHERE telegram_user_id = ? AND status IN ("pending", "submitted")', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching active donation: {e}")
            return None

    def get_donation_stats(self):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM donations WHERE status = "completed"')
            completed = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(amount) FROM donations WHERE status = "completed"')
            total = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM donations WHERE status = "pending"')
            pending = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT telegram_user_id) FROM donations WHERE status = "completed"')
            unique_donors = cursor.fetchone()[0]
            
            conn.close()
            return {
                'completed': completed,
                'total': total,
                'pending': pending,
                'unique_donors': unique_donors
            }
        except Exception as e:
            logger.error(f"Error fetching donation stats: {e}")
            return {'completed': 0, 'total': 0, 'pending': 0, 'unique_donors': 0}

    def get_recent_donations(self, limit=10):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT random_id, donor_name, amount, donation_item, timestamp 
                FROM donations 
                WHERE status = "completed" 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error fetching recent donations: {e}")
            return []
