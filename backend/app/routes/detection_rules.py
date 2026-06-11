from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.detection_rule import DetectionRule
from pydantic import BaseModel

router = APIRouter()


class DetectionRuleCreate(BaseModel):
    pattern: str  # Regex pattern
    category_id: int | None = None
    requires_confirmation: bool = True


class DetectionRuleResponse(BaseModel):
    id: int
    user_id: int
    pattern: str
    category_id: int | None = None
    requires_confirmation: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=DetectionRuleResponse)
def create_rule(user_id: int, rule_data: DetectionRuleCreate, db: Session = Depends(get_db)):
    """Create a new detection rule"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rule = DetectionRule(
        user_id=user_id,
        pattern=rule_data.pattern,
        category_id=rule_data.category_id,
        requires_confirmation=rule_data.requires_confirmation,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{user_id}", response_model=list[DetectionRuleResponse])
def get_user_rules(user_id: int, db: Session = Depends(get_db)):
    """Get all detection rules for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rules = db.query(DetectionRule).filter(DetectionRule.user_id == user_id).all()
    return rules


@router.patch("/{rule_id}", response_model=DetectionRuleResponse)
def update_rule(rule_id: int, rule_data: DetectionRuleCreate, db: Session = Depends(get_db)):
    """Update a detection rule"""
    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.pattern = rule_data.pattern
    rule.category_id = rule_data.category_id
    rule.requires_confirmation = rule_data.requires_confirmation
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a detection rule"""
    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}
