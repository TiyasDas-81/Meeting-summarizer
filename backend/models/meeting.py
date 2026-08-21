import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from backend.database.db import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    duration = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Store lists/dicts as JSON text in SQLite for maximum portability
    _key_points = Column("key_points", Text, nullable=True, default="[]")
    _decisions = Column("decisions", Text, nullable=True, default="[]")
    _action_items = Column("action_items", Text, nullable=True, default="[]")
    
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def key_points(self):
        try:
            return json.loads(self._key_points) if self._key_points else []
        except Exception:
            return []

    @key_points.setter
    def key_points(self, value):
        self._key_points = json.dumps(value or [])

    @property
    def decisions(self):
        try:
            return json.loads(self._decisions) if self._decisions else []
        except Exception:
            return []

    @decisions.setter
    def decisions(self, value):
        self._decisions = json.dumps(value or [])

    @property
    def action_items(self):
        try:
            return json.loads(self._action_items) if self._action_items else []
        except Exception:
            return []

    @action_items.setter
    def action_items(self, value):
        self._action_items = json.dumps(value or [])
