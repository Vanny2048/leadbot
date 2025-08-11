from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from .config import settings

Base = declarative_base()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(String(255))
    phone = Column(String(64))
    email = Column(String(255))
    source = Column(String(255), default="manual")
    notes = Column(Text, default="")
    status = Column(String(64), default="new")  # new, qualified, unqualified, contacted, booked
    interested_services = Column(String(255), default="")  # veneers,invisalign,whitening
    budget = Column(String(64), default="")
    timeline = Column(String(64), default="")

    interactions = relationship("Interaction", back_populates="lead", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    channel = Column(String(64))  # call, sms, email, chat, system
    direction = Column(String(16), default="outbound")  # inbound/outbound/system
    content = Column(Text, default="")

    lead = relationship("Lead", back_populates="interactions")


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)
    value = Column(Text)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_setting(db, key: str, value: str) -> None:
    existing = db.query(Setting).filter(Setting.key == key).first()
    if existing:
        existing.value = value
    else:
        s = Setting(key=key, value=value)
        db.add(s)
    db.commit()


def get_setting(db, key: str) -> Optional[str]:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s else None