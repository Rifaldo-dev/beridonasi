import sqlite3
import requests
from config import DATABASE_NAME
from common import get_logger, QRISException

logger = get_logger(__name__)

class QRISService:
    def __init__(self):
        self.db_name = DATABASE_NAME
        self.api_url = "https://api-mininxd.vercel.app/qris"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def validate_qris_code(self, qris_code):
        if len(qris_code) < 50 or not qris_code.startswith('00020'):
            raise QRISException("QRIS code is invalid or incomplete")
        return True

    def generate_qris(self, qris_code, amount):
        try:
            self.validate_qris_code(qris_code)
            api_url = f"{self.api_url}?qris={qris_code}&nominal={amount}"
            response = requests.get(api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and 'QR' in data and data['QR']:
                qr_data = data['QR']
                if (qr_data.startswith('00020101') or qr_data.startswith('00020201')) and len(qr_data) > 100 and '5204' in qr_data:
                    logger.info(f"QRIS generated successfully for amount Rp {amount:,}")
                    return data
            
            logger.warning(f"Invalid QRIS response for amount Rp {amount:,}")
            raise QRISException("QRIS generation failed - Invalid response")
        except requests.RequestException as e:
            logger.error(f"QRIS API error: {e}")
            raise QRISException(f"QRIS API error: {str(e)}")
        except Exception as e:
            logger.error(f"QRIS generation error: {e}")
            raise QRISException(f"QRIS generation failed: {str(e)}")

    def save_qris_code(self, qris_code):
        try:
            self.validate_qris_code(qris_code)
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('donation_qris', qris_code))
            conn.commit()
            conn.close()
            logger.warning(f"QRIS code saved")
        except Exception as e:
            logger.error(f"Error saving QRIS code: {e}")
            raise

    def load_qris_code(self):
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', ('donation_qris',))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error loading QRIS code: {e}")
            return None

    def test_qris_generation(self, qris_code, test_amount=1000):
        try:
            result = self.generate_qris(qris_code, test_amount)
            logger.info(f"QRIS test successful for code")
            return result is not None
        except Exception as e:
            logger.error(f"QRIS test failed: {e}")
            return False
