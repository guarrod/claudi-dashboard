from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("expense_templates.id"), nullable=True)

    concept = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="PLANNED")  # PLANNED, COMPLETED, CANCELLED
    transaction_type = Column(String, default="EXPENSE")  # EXPENSE, SAVINGS_TRANSFER, INCOME
    completion_method = Column(String, nullable=True)  # MANUAL, DETECTED_VALIDATED, AUTO
    detected_in_email = Column(String, nullable=True)  # Email ID if detected

    planned_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="transactions")
    sprint = relationship("Sprint", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    template = relationship("ExpenseTemplate", back_populates="transactions")
