from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class CardStatement(Base):
    __tablename__ = "card_statements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_name = Column(String, nullable=False)  # Nombre de la tarjeta
    available_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=True)
    active_balance = Column(Float, nullable=True)
    statement_date = Column(DateTime, nullable=False)
    email_id = Column(String, nullable=True)
    source = Column(String, default="email")  # email o manual

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
