from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime

class ActionItemSchema(BaseModel):
    task: str = Field(description="Description of the task to be completed")
    owner: str = Field(default="Unassigned", description="Name of person responsible if mentioned, else Unassigned")
    deadline: str = Field(default="TBD", description="Deadline date/time if mentioned, else TBD")
    priority: str = Field(default="Medium", description="Priority level: High, Medium, or Low")

    @field_validator("owner", mode="before")
    @classmethod
    def validate_owner(cls, v):
        if v is None or str(v).strip().lower() in ["", "null", "none", "unknown", "n/a"]:
            return "Unassigned"
        return str(v).strip()

    @field_validator("deadline", mode="before")
    @classmethod
    def validate_deadline(cls, v):
        if v is None or str(v).strip().lower() in ["", "null", "none", "unknown", "n/a", "tbd"]:
            return "TBD"
        return str(v).strip()

class MeetingAnalysisSchema(BaseModel):
    summary: str = Field(description="Concise 2-4 sentence executive summary of the meeting")
    key_points: List[str] = Field(default_factory=list, description="Key discussion points raised during meeting")
    decisions: List[str] = Field(default_factory=list, description="Explicit decisions agreed upon")
    action_items: List[ActionItemSchema] = Field(default_factory=list, description="List of actionable tasks")

class MeetingCreateSchema(BaseModel):
    title: Optional[str] = None

class MeetingResponseSchema(BaseModel):
    id: str
    title: str
    filename: str
    file_size: int
    status: str
    duration: Optional[float] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_points: List[str] = []
    decisions: List[str] = []
    action_items: List[ActionItemSchema] = []
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
