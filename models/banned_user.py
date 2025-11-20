from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from core import Base

class BannedUser(Base):
    __tablename__ = "banned_users"
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(255))
    banned_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(500), default="Bermain-main dengan sistem donasi")
    
    def __repr__(self):
        return f"<BannedUser {self.user_id}>"
