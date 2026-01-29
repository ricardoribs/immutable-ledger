from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime

from src.infra.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    channel = Column(String, nullable=False)  # EMAIL, SMS, PUSH, WHATSAPP
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="SENT")
    created_at = Column(DateTime, default=datetime.utcnow)
