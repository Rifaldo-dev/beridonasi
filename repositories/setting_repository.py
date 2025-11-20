from sqlalchemy.orm import Session
from models import Setting

class SettingRepository:
    @staticmethod
    def set(db: Session, key: str, value: str) -> Setting:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting
    
    @staticmethod
    def get(db: Session, key: str) -> str:
        setting = db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else None
    
    @staticmethod
    def get_all(db: Session):
        return db.query(Setting).all()
