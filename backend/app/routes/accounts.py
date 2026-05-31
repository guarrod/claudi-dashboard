from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.account import Account
from pydantic import BaseModel

router = APIRouter()


class AccountCreate(BaseModel):
    name: str
    account_type: str  # BANK, CASH, CREDIT_CARD
    current_balance: float = 0.0


class AccountResponse(BaseModel):
    id: int
    user_id: int
    name: str
    account_type: str
    current_balance: float
    available_balance: float

    class Config:
        from_attributes = True


@router.post("/", response_model=AccountResponse)
def create_account(user_id: int, account_data: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    account = Account(
        user_id=user_id,
        name=account_data.name,
        account_type=account_data.account_type,
        current_balance=account_data.current_balance,
        available_balance=account_data.current_balance,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{user_id}", response_model=list[AccountResponse])
def get_user_accounts(user_id: int, db: Session = Depends(get_db)):
    """Get all accounts for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    return accounts


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int, account_data: AccountCreate, db: Session = Depends(get_db)
):
    """Update an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.name = account_data.name
    account.account_type = account_data.account_type
    account.current_balance = account_data.current_balance
    db.commit()
    db.refresh(account)
    return account


@router.patch("/{account_id}/balance")
def update_account_balance(account_id: int, amount: float, db: Session = Depends(get_db)):
    """Update account balance"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.current_balance = amount
    account.available_balance = amount  # Reset available balance when current changes

    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}


@router.post("/{account_id}/recalculate-balance")
def recalculate_balance(account_id: int, db: Session = Depends(get_db)):
    """Recalculate available balance for account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    from models.transaction import Transaction

    # Sum of completed expenses
    completed_sum = (
        db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.status == "COMPLETED",
            Transaction.transaction_type == "EXPENSE",
        ).with_entities(db.func.sum(Transaction.amount)).scalar() or 0
    )

    account.available_balance = account.current_balance - completed_sum
    db.commit()
    db.refresh(account)

    return {
        "account_id": account.id,
        "current_balance": account.current_balance,
        "available_balance": account.available_balance,
    }
