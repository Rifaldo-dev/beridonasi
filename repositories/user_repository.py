from sqlalchemy.orm import Session
from models import BannedUser, CustomDonationItem

class UserRepository:
    @staticmethod
    def ban_user(db: Session, user_id: int, username: str = "", reason: str = "") -> BannedUser:
        banned_user = BannedUser(
            user_id=user_id,
            username=username,
            reason=reason or "Bermain-main dengan sistem donasi"
        )
        db.add(banned_user)
        db.commit()
        db.refresh(banned_user)
        return banned_user
    
    @staticmethod
    def unban_user(db: Session, user_id: int) -> bool:
        banned_user = db.query(BannedUser).filter(BannedUser.user_id == user_id).first()
        if banned_user:
            db.delete(banned_user)
            db.commit()
            return True
        return False
    
    @staticmethod
    def is_banned(db: Session, user_id: int) -> bool:
        return db.query(BannedUser).filter(BannedUser.user_id == user_id).first() is not None
    
    @staticmethod
    def get_banned_users(db: Session):
        return db.query(BannedUser).all()
    
    @staticmethod
    def add_custom_item(db: Session, item_name: str, price: int, created_by: int) -> CustomDonationItem:
        custom_item = CustomDonationItem(
            item_name=item_name,
            price=price,
            created_by=created_by
        )
        db.add(custom_item)
        db.commit()
        db.refresh(custom_item)
        return custom_item
    
    @staticmethod
    def get_custom_items(db: Session):
        return db.query(CustomDonationItem).all()
    
    @staticmethod
    def get_all_items_for_random(db: Session):
        from config import DONATION_ITEMS
        all_items = []
        for category_items in DONATION_ITEMS.values():
            all_items.extend(category_items)
        
        custom_items = db.query(CustomDonationItem).all()
        for item in custom_items:
            all_items.append(item.item_name)
        
        return all_items
