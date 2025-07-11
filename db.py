from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum as SAEnum,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = "sqlite:///./complaints.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


class Status(str, Enum):
    open = "open"
    closed = "closed"


class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class Category(str, Enum):
    technical = "technical"
    payment = "payment"
    other = "other"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    status = Column(SAEnum(Status), default=Status.open, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    sentiment = Column(SAEnum(Sentiment))
    category = Column(SAEnum(Category), default=Category.other)


Base.metadata.create_all(bind=engine)
