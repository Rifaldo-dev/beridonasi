from sqlalchemy import Column, String
from core import Base

class Setting(Base):
    __tablename__ = "settings"
    
    key = Column(String(255), primary_key=True)
    value = Column(String(500))
    
    def __repr__(self):
        return f"<Setting {self.key}>"
