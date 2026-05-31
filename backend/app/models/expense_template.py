from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class ExpenseTemplate(Base):
    __tablename__ = "expense_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    name = Column(String, nullable=False)  # "Netflix", "Renta", etc.
    amount = Column(Float, nullable=False)
    frequency = Column(String, default="MONTHLY")  # MONTHLY, BIWEEKLY, OTHER
    is_fixed = Column(String, default=True)  # True if recurring

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="templates")
    category = relationship("Category")
    transactions = relationship("Transaction", back_populates="template")
