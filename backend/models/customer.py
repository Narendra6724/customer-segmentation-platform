"""
Customer ORM model.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from backend.database.db import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, unique=True, nullable=False, index=True)
    income = Column(Float, nullable=False)
    spending = Column(Float, nullable=False)
    cluster = Column(Integer, nullable=False)
    insight = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "income": self.income,
            "spending": self.spending,
            "cluster": self.cluster,
            "insight": self.insight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
