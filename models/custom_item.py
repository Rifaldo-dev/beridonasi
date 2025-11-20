from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from core import Base

class CustomDonationItem(Base):
    __tablename__ = "custom_donation_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CustomDonationItem {self.item_name}>"
