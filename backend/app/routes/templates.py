from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.expense_template import ExpenseTemplate
from app.models.sprint import Sprint
from app.models.transaction import Transaction
from pydantic import BaseModel

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    amount: float
    category_id: int | None = None
    frequency: str = "MONTHLY"  # MONTHLY, BIWEEKLY, OTHER


class TemplateResponse(BaseModel):
    id: int
    user_id: int
    name: str
    amount: float
    category_id: int | None = None
    frequency: str
    is_fixed: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=TemplateResponse)
def create_template(user_id: int, template_data: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new expense template (fixed/recurring)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    template = ExpenseTemplate(
        user_id=user_id,
        name=template_data.name,
        amount=template_data.amount,
        category_id=template_data.category_id,
        frequency=template_data.frequency,
        is_fixed=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{user_id}", response_model=list[TemplateResponse])
def get_user_templates(user_id: int, db: Session = Depends(get_db)):
    """Get all templates for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    templates = db.query(ExpenseTemplate).filter(ExpenseTemplate.user_id == user_id).all()
    return templates


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int, template_data: TemplateCreate, db: Session = Depends(get_db)
):
    """Update an expense template"""
    template = db.query(ExpenseTemplate).filter(ExpenseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.name = template_data.name
    template.amount = template_data.amount
    template.category_id = template_data.category_id
    template.frequency = template_data.frequency
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete an expense template"""
    template = db.query(ExpenseTemplate).filter(ExpenseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}


@router.post("/{template_id}/duplicate/{sprint_id}")
def duplicate_template_to_sprint(
    template_id: int, sprint_id: int, user_id: int, db: Session = Depends(get_db)
):
    """Duplicate a template into a sprint as a transaction"""
    template = db.query(ExpenseTemplate).filter(ExpenseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Create transaction from template
    transaction = Transaction(
        user_id=user_id,
        sprint_id=sprint_id,
        account_id=None,  # User must select account
        category_id=template.category_id,
        template_id=template_id,
        concept=template.name,
        amount=template.amount,
        status="PLANNED",
        transaction_type="EXPENSE",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "message": "Template duplicated to sprint",
        "transaction_id": transaction.id,
        "concept": transaction.concept,
        "amount": transaction.amount,
    }


class ApplyTemplatesRequest(BaseModel):
    template_ids: list[int]
    account_id: int | None = None


@router.post("/{sprint_id}/apply-templates")
def apply_templates_to_sprint(
    sprint_id: int, user_id: int, data: ApplyTemplatesRequest, db: Session = Depends(get_db)
):
    """Apply multiple templates to a sprint at once"""
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    created_transactions = []

    for template_id in data.template_ids:
        template = db.query(ExpenseTemplate).filter(
            ExpenseTemplate.id == template_id,
            ExpenseTemplate.user_id == user_id,
        ).first()

        if template:
            transaction = Transaction(
                user_id=user_id,
                sprint_id=sprint_id,
                account_id=data.account_id,
                category_id=template.category_id,
                template_id=template_id,
                concept=template.name,
                amount=template.amount,
                status="PLANNED",
                transaction_type="EXPENSE",
            )
            db.add(transaction)
            created_transactions.append(
                {
                    "id": template.id,
                    "name": template.name,
                    "amount": template.amount,
                }
            )

    db.commit()

    return {
        "message": f"Applied {len(created_transactions)} templates",
        "count": len(created_transactions),
        "templates": created_transactions,
    }


@router.get("/{sprint_id}/suggested-templates")
def get_suggested_templates_for_sprint(
    sprint_id: int, user_id: int, db: Session = Depends(get_db)
):
    """Get templates that were used in previous sprints"""
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Get templates that have been used before
    used_templates = (
        db.query(ExpenseTemplate)
        .join(Transaction, ExpenseTemplate.id == Transaction.template_id)
        .filter(
            ExpenseTemplate.user_id == user_id,
            Transaction.user_id == user_id,
        )
        .distinct(ExpenseTemplate.id)
        .all()
    )

    return [
        {
            "id": t.id,
            "name": t.name,
            "amount": t.amount,
            "frequency": t.frequency,
            "category_id": t.category_id,
        }
        for t in used_templates
    ]
