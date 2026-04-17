from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from models.base import Base


class AIConfigVersion(Base):
    __tablename__ = "ai_config_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)  # e.g. "chatbot", "report_analyzer"
    version = Column(Integer)

    # 🔥 unified config
    prompt = Column(Text)
    model = Column(String)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)

    status = Column(String, default="draft")  # draft / approved / rejected
    is_active = Column(Boolean, default=False)

    created_by = Column(String)
    approved_by = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)