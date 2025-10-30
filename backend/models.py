from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .db import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company = Column(String, nullable=False)
    leverage = Column(Integer, nullable=False)
    trade_type = Column(String, nullable=False)  # 'leverage' | 'inverse'
    quantity = Column(Integer, nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    stage = Column(Integer, nullable=False, default=0)
    max_stage = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    club_name = Column(String, nullable=True)
    total_assets = Column(Integer, nullable=True)
