from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from database import Base


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sprint_number = Column(Integer)  # 1 or 2
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_budget = Column(Float, default=0.0)
    status = Column(String, default="ACTIVE")  # ACTIVE, COMPLETED

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sprints")
    transactions = relationship("Transaction", back_populates="sprint", cascade="all, delete-orphan")
