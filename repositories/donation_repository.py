from sqlalchemy.orm import Session
from models import Donation
from datetime import datetime

class DonationRepository:
    @staticmethod
    def create(db: Session, random_id: str, amount: int, donation_item: str, 
               telegram_user_id: int, telegram_username: str = "") -> Donation:
        donation = Donation(
            random_id=random_id,
            amount=amount,
            donation_item=donation_item,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            status="pending"
        )
        db.add(donation)
        db.commit()
        db.refresh(donation)
        return donation
    
    @staticmethod
    def get_by_id(db: Session, donation_id: int) -> Donation:
        return db.query(Donation).filter(Donation.id == donation_id).first()
    
    @staticmethod
    def get_by_random_id(db: Session, random_id: str) -> Donation:
        return db.query(Donation).filter(Donation.random_id == random_id).first()
    
    @staticmethod
    def update(db: Session, donation_id: int, **kwargs) -> Donation:
        donation = db.query(Donation).filter(Donation.id == donation_id).first()
        if donation:
            for key, value in kwargs.items():
                setattr(donation, key, value)
            db.commit()
            db.refresh(donation)
        return donation
    
    @staticmethod
    def get_by_user(db: Session, telegram_user_id: int, status: str = None):
        query = db.query(Donation).filter(Donation.telegram_user_id == telegram_user_id)
        if status:
            query = query.filter(Donation.status == status)
        return query.all()
    
    @staticmethod
    def get_pending_by_user(db: Session, telegram_user_id: int) -> Donation:
        return db.query(Donation).filter(
            Donation.telegram_user_id == telegram_user_id,
            Donation.status.in_(["pending", "submitted"])
        ).first()
    
    @staticmethod
    def get_all(db: Session, status: str = None, limit: int = None):
        query = db.query(Donation)
        if status:
            query = query.filter(Donation.status == status)
        query = query.order_by(Donation.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        return db.query(Donation).filter(Donation.status == status).count()
    
    @staticmethod
    def get_total_amount(db: Session, status: str = "verified") -> int:
        result = db.query(Donation).filter(Donation.status == status)
        return sum(d.amount for d in result.all()) or 0
