from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
from models.transaction import Transaction
from models.sprint import Sprint
from models.account import Account
from models.user import User
from pydantic import BaseModel

router = APIRouter()


class TransactionCreate(BaseModel):
    sprint_id: int
    account_id: int
    concept: str
    amount: float
    category_id: int = None
    template_id: int = None
    transaction_type: str = "EXPENSE"
    planned_date: date = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    sprint_id: int
    account_id: int
    concept: str
    amount: float
    status: str
    transaction_type: str
    completion_method: str = None
    planned_date: date = None
    completed_date: date = None

    class Config:
        from_attributes = True


@router.post("/", response_model=TransactionResponse)
def create_transaction(user_id: int, transaction_data: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sprint = db.query(Sprint).filter(Sprint.id == transaction_data.sprint_id, Sprint.user_id == user_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    account = db.query(Account).filter(Account.id == transaction_data.account_id, Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transaction = Transaction(
        user_id=user_id,
        sprint_id=transaction_data.sprint_id,
        account_id=transaction_data.account_id,
        concept=transaction_data.concept,
        amount=transaction_data.amount,
        category_id=transaction_data.category_id,
        template_id=transaction_data.template_id,
        transaction_type=transaction_data.transaction_type,
        planned_date=transaction_data.planned_date,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Recalculate account balance
    _recalculate_available_balance(db, account.id)

    return transaction


@router.get("/{sprint_id}", response_model=list[TransactionResponse])
def get_sprint_transactions(user_id: int, sprint_id: int, db: Session = Depends(get_db)):
    """Get all transactions for a sprint"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.user_id == user_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    transactions = db.query(Transaction).filter(Transaction.sprint_id == sprint_id).all()
    return transactions


@router.patch("/{transaction_id}/complete")
def complete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Mark transaction as completed"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.status = "COMPLETED"
    transaction.completed_date = date.today()
    transaction.completion_method = "MANUAL"
    db.commit()
    db.refresh(transaction)

    # Recalculate account balance
    _recalculate_available_balance(db, transaction.account_id)

    return transaction


@router.patch("/{transaction_id}/uncomplete")
def uncomplete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Mark transaction as not completed (return to PLANNED)"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.status = "PLANNED"
    transaction.completed_date = None
    db.commit()
    db.refresh(transaction)

    # Recalculate account balance
    _recalculate_available_balance(db, transaction.account_id)

    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    account_id = transaction.account_id
    db.delete(transaction)
    db.commit()

    # Recalculate account balance
    _recalculate_available_balance(db, account_id)

    return {"message": "Transaction deleted"}


def _recalculate_available_balance(db: Session, account_id: int):
    """Helper function to recalculate available balance for an account"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if account:
        # Sum of completed transactions
        completed_sum = (
            db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.status == "COMPLETED",
                Transaction.transaction_type == "EXPENSE",
            ).with_entities(db.func.sum(Transaction.amount)).scalar() or 0
        )

        account.available_balance = account.current_balance - completed_sum
        db.commit()
