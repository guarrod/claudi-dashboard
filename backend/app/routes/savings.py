from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.sprint import Sprint
from app.models.transaction import Transaction
from app.models.savings import SavingsMovement
from pydantic import BaseModel

router = APIRouter()


class SavingsMovementCreate(BaseModel):
    account_id: int
    amount: float
    description: str | None = None


class SavingsMovementResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    movement_type: str
    description: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class SavingsBalanceResponse(BaseModel):
    total_savings: float
    last_movement: str | None = None


@router.post("/move", response_model=SavingsMovementResponse)
def move_to_savings(
    user_id: int, data: SavingsMovementCreate, db: Session = Depends(get_db)
):
    """Move amount to savings from specified account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    account = db.query(Account).filter(
        Account.id == data.account_id, Account.user_id == user_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Create savings movement
    movement = SavingsMovement(
        user_id=user_id,
        account_id=data.account_id,
        amount=data.amount,
        movement_type="DEPOSIT",
        description=data.description or f"Transfer from {account.name}",
    )
    db.add(movement)

    # Update account balance
    account.current_balance -= data.amount
    account.available_balance -= data.amount

    db.commit()
    db.refresh(movement)
    return movement


@router.get("/balance/{user_id}", response_model=SavingsBalanceResponse)
def get_savings_balance(user_id: int, db: Session = Depends(get_db)):
    """Get user's total savings balance"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_deposits = db.query(func.sum(SavingsMovement.amount)).filter(
        SavingsMovement.user_id == user_id,
        SavingsMovement.movement_type == "DEPOSIT"
    ).scalar() or 0.0

    total_withdrawals = db.query(func.sum(SavingsMovement.amount)).filter(
        SavingsMovement.user_id == user_id,
        SavingsMovement.movement_type == "WITHDRAWAL"
    ).scalar() or 0.0

    total_savings = total_deposits - total_withdrawals

    last_movement = db.query(SavingsMovement).filter(
        SavingsMovement.user_id == user_id
    ).order_by(SavingsMovement.created_at.desc()).first()

    return {
        "total_savings": total_savings,
        "last_movement": last_movement.created_at.isoformat() if last_movement else None,
    }


@router.get("/history/{user_id}")
def get_savings_history(user_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get user's savings movement history"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    movements = db.query(SavingsMovement).filter(
        SavingsMovement.user_id == user_id
    ).order_by(SavingsMovement.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": m.id,
            "amount": m.amount,
            "type": m.movement_type,
            "description": m.description,
            "date": m.created_at.isoformat(),
        }
        for m in movements
    ]


class SprintSuggestSavingsResponse(BaseModel):
    sprint_id: int
    remaining_balance: float
    account_id: int
    account_name: str


@router.get("/{sprint_id}/suggest-savings", response_model=SprintSuggestSavingsResponse)
def suggest_savings_for_sprint(
    sprint_id: int, user_id: int, account_id: int, db: Session = Depends(get_db)
):
    """Get savings suggestion for completing a sprint"""
    sprint = db.query(Sprint).filter(
        Sprint.id == sprint_id, Sprint.user_id == user_id
    ).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    account = db.query(Account).filter(
        Account.id == account_id, Account.user_id == user_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    remaining = account.available_balance
    if remaining <= 0:
        raise HTTPException(
            status_code=400,
            detail="No remaining balance to save"
        )

    return {
        "sprint_id": sprint_id,
        "remaining_balance": remaining,
        "account_id": account_id,
        "account_name": account.name,
    }


@router.post("/{sprint_id}/complete-and-save")
def complete_sprint_and_save(
    sprint_id: int,
    user_id: int,
    account_id: int,
    save_amount: float | None = None,
    db: Session = Depends(get_db)
):
    """Complete sprint and optionally move remaining balance to savings"""
    sprint = db.query(Sprint).filter(
        Sprint.id == sprint_id, Sprint.user_id == user_id
    ).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    account = db.query(Account).filter(
        Account.id == account_id, Account.user_id == user_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Mark sprint as completed
    sprint.status = "COMPLETED"

    # Move savings if amount specified
    if save_amount and save_amount > 0:
        if save_amount > account.available_balance:
            raise HTTPException(
                status_code=400,
                detail="Save amount exceeds available balance"
            )

        movement = SavingsMovement(
            user_id=user_id,
            sprint_id=sprint_id,
            account_id=account_id,
            amount=save_amount,
            movement_type="DEPOSIT",
            description=f"Sprint {sprint.sprint_number} savings",
        )
        db.add(movement)

        # Update account balance
        account.current_balance -= save_amount
        account.available_balance -= save_amount

    db.commit()

    return {
        "sprint_id": sprint_id,
        "status": "COMPLETED",
        "saved_amount": save_amount or 0,
        "message": "Sprint completed successfully",
    }
