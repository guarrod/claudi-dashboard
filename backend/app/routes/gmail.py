from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models.user import User
from models.card_statement import CardStatement
from models.notification import Notification
from services.gmail_service import GmailService
from pydantic import BaseModel

router = APIRouter()


class CardStatementResponse(BaseModel):
    id: int
    user_id: int
    card_name: str
    available_balance: float
    current_balance: float = None
    active_balance: float = None
    statement_date: str

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: str
    content: str
    status: str

    class Config:
        from_attributes = True


@router.post("/sync")
def sync_gmail_emails(user_id: int, days_back: int = 7, db: Session = Depends(get_db)):
    """Sync emails from Gmail"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.google_refresh_token:
        raise HTTPException(status_code=400, detail="User has not authorized Gmail access")

    try:
        gmail_service = GmailService(user)
        synced_count = gmail_service.sync_emails(db, days_back=days_back)

        return {
            "message": f"Synced {synced_count} transactions",
            "count": synced_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing Gmail: {str(e)}")


@router.get("/cards/{user_id}", response_model=list[CardStatementResponse])
def get_card_statements(user_id: int, db: Session = Depends(get_db)):
    """Get latest card statements for user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    statements = (
        db.query(CardStatement)
        .filter(CardStatement.user_id == user_id)
        .order_by(CardStatement.statement_date.desc())
        .limit(10)
        .all()
    )

    return statements


@router.post("/sync-cards")
def sync_card_statements(user_id: int, db: Session = Depends(get_db)):
    """Sync credit card statements from Gmail"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.google_refresh_token:
        raise HTTPException(status_code=400, detail="User has not authorized Gmail access")

    try:
        gmail_service = GmailService(user)

        # Get card statement
        statement_data = gmail_service.get_card_statement(db)

        if not statement_data:
            return {"message": "No card statement found"}

        # Save to DB
        statement = CardStatement(
            user_id=user_id,
            card_name="Tarjeta de Crédito",  # TODO: detect from email
            available_balance=statement_data["available"],
            statement_date=datetime.utcnow(),
            email_id=statement_data.get("email_id"),
            source="email",
        )
        db.add(statement)
        db.commit()
        db.refresh(statement)

        return {
            "message": "Card statement synced",
            "available": statement_data["available"],
            "statement_id": statement.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error syncing card statement: {str(e)}"
        )


@router.get("/notifications/{user_id}", response_model=list[NotificationResponse])
def get_notifications(user_id: int, status: str = "PENDING", db: Session = Depends(get_db)):
    """Get notifications for user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.status == status)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return notifications


@router.post("/notifications/{notification_id}/confirm")
def confirm_notification(notification_id: int, db: Session = Depends(get_db)):
    """Confirm a detected transaction"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.status = "CONFIRMED"
    db.commit()
    db.refresh(notification)

    return {"message": "Notification confirmed", "notification_id": notification.id}


@router.post("/notifications/{notification_id}/discard")
def discard_notification(notification_id: int, db: Session = Depends(get_db)):
    """Discard a detected transaction"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.status = "DISCARDED"
    db.commit()
    db.refresh(notification)

    return {"message": "Notification discarded", "notification_id": notification.id}
