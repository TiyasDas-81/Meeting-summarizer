import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.db import Base
from backend.models.meeting import Meeting

def test_meeting_orm_model_crud():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Create meeting
    meeting = Meeting(
        title="Architecture Review",
        filename="arch_review.wav",
        file_path="uploads/arch_review.wav",
        file_size=1024,
        status="COMPLETED",
        summary="Reviewed backend DB schema",
        key_points=["Point A", "Point B"],
        decisions=["Decision 1"],
        action_items=[{"task": "Update schema", "owner": "John", "deadline": "Friday", "priority": "High"}]
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    assert meeting.id is not None
    assert meeting.key_points == ["Point A", "Point B"]
    assert meeting.decisions == ["Decision 1"]
    assert len(meeting.action_items) == 1
    assert meeting.action_items[0]["owner"] == "John"

    # Query meeting
    fetched = db.query(Meeting).filter(Meeting.id == meeting.id).first()
    assert fetched is not None
    assert fetched.title == "Architecture Review"

    # Delete meeting
    db.delete(fetched)
    db.commit()
    assert db.query(Meeting).filter(Meeting.id == meeting.id).first() is None
