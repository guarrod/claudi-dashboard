from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models.sprint import Sprint
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class SprintCreate(BaseModel):
    sprint_number: int
    start_date: date
    end_date: date
    total_budget: float = 0.0


class SprintResponse(BaseModel):
    id: int
    user_id: int
    sprint_number: int
    start_date: date
    end_date: date
    total_budget: float
    status: str

    class Config:
        from_attributes = True


@router.post("/", response_model=SprintResponse)
def create_sprint(user_id: int, sprint_data: SprintCreate, db: Session = Depends(get_db)):
    """Create a new sprint"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sprint = Sprint(
        user_id=user_id,
        sprint_number=sprint_data.sprint_number,
        start_date=sprint_data.start_date,
        end_date=sprint_data.end_date,
        total_budget=sprint_data.total_budget,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get("/{user_id}", response_model=list[SprintResponse])
def get_user_sprints(user_id: int, db: Session = Depends(get_db)):
    """Get all sprints for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sprints = db.query(Sprint).filter(Sprint.user_id == user_id).all()
    return sprints


@router.get("/{user_id}/active", response_model=SprintResponse)
def get_active_sprint(user_id: int, db: Session = Depends(get_db)):
    """Get current/active sprint for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()
    sprint = (
        db.query(Sprint)
        .filter(
            Sprint.user_id == user_id,
            Sprint.start_date <= today,
            Sprint.end_date >= today,
            Sprint.status == "ACTIVE",
        )
        .first()
    )

    if not sprint:
        raise HTTPException(status_code=404, detail="No active sprint found")

    return sprint


@router.post("/{user_id}/auto-create")
def auto_create_sprints(user_id: int, db: Session = Depends(get_db)):
    """Auto-create sprints for next month (quincenales)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()

    # Sprint 1: Day 1-15
    sprint1_start = date(today.year, today.month, 1)
    sprint1_end = date(today.year, today.month, 15)

    # Sprint 2: Day 16-last day
    if today.month == 12:
        sprint2_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        sprint2_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    sprint2_start = date(today.year, today.month, 16)

    sprints_created = []

    # Check and create Sprint 1
    sprint1 = db.query(Sprint).filter(
        Sprint.user_id == user_id,
        Sprint.sprint_number == 1,
        Sprint.start_date == sprint1_start,
    ).first()

    if not sprint1:
        sprint1 = Sprint(
            user_id=user_id,
            sprint_number=1,
            start_date=sprint1_start,
            end_date=sprint1_end,
        )
        db.add(sprint1)
        sprints_created.append(sprint1)

    # Check and create Sprint 2
    sprint2 = db.query(Sprint).filter(
        Sprint.user_id == user_id,
        Sprint.sprint_number == 2,
        Sprint.start_date == sprint2_start,
    ).first()

    if not sprint2:
        sprint2 = Sprint(
            user_id=user_id,
            sprint_number=2,
            start_date=sprint2_start,
            end_date=sprint2_end,
        )
        db.add(sprint2)
        sprints_created.append(sprint2)

    db.commit()

    return {
        "message": f"Created {len(sprints_created)} sprints",
        "sprints": [{"sprint_number": s.sprint_number, "start_date": s.start_date, "end_date": s.end_date} for s in sprints_created],
    }


@router.patch("/{sprint_id}/complete")
def complete_sprint(sprint_id: int, db: Session = Depends(get_db)):
    """Mark sprint as completed"""
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    sprint.status = "COMPLETED"
    db.commit()
    db.refresh(sprint)

    return {"message": "Sprint completed", "sprint_id": sprint.id}
