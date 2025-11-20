from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from core import Base

class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    random_id = Column(String(50), unique=True, nullable=False)
    donor_name = Column(String(255), default="")
    message = Column(Text, default="")
    amount = Column(Integer, nullable=False)
    donation_item = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    qris_id = Column(String(255))
    telegram_user_id = Column(Integer)
    telegram_username = Column(String(255), default="")
    
    def __repr__(self):
        return f"<Donation {self.random_id}: {self.amount} by {self.donor_name or 'Anonymous'}>"
