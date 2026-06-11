from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import Category
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class CategoryCreate(BaseModel):
    name: str
    color: str = "#007AFF"


class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    color: str

    class Config:
        from_attributes = True


@router.post("/", response_model=CategoryResponse)
def create_category(user_id: int, category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    category = Category(
        user_id=user_id,
        name=category_data.name,
        color=category_data.color,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{user_id}", response_model=list[CategoryResponse])
def get_user_categories(user_id: int, db: Session = Depends(get_db)):
    """Get all categories for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    categories = db.query(Category).filter(Category.user_id == user_id).all()
    return categories


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Update a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = category_data.name
    category.color = category_data.color
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}
