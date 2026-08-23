import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.meeting import Meeting
from backend.schemas.meeting import MeetingResponseSchema
from backend.services.transcription import SUPPORTED_FORMATS, validate_audio_file
from backend.services.meeting_processor import process_meeting
from backend.config import get_settings

MEDIA_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".aac": "audio/aac",
}

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])

@router.post("/upload", response_model=MeetingResponseSchema, status_code=status.HTTP_201_CREATED)
def upload_meeting(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload an audio file, validate, transcribe, analyze with LLM, and store results.
    """
    settings = get_settings()
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    # Generate unique filename
    meeting_id = str(uuid.uuid4())
    save_filename = f"{meeting_id}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    # Save uploaded file content
    try:
        content = file.file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB.")

        with open(save_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {str(e)}")

    meeting_title = title.strip() if title and title.strip() else os.path.splitext(file.filename)[0]

    # Create DB entry
    meeting = Meeting(
        id=meeting_id,
        title=meeting_title,
        filename=file.filename,
        file_path=save_path,
        file_size=file_size,
        status="PENDING"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # Execute processing pipeline
    processed_meeting = process_meeting(meeting.id, db)
    return processed_meeting

@router.get("", response_model=List[MeetingResponseSchema])
def list_meetings(db: Session = Depends(get_db)):
    """Retrieve all processed meetings sorted by creation date."""
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return meetings

@router.get("/{meeting_id}", response_model=MeetingResponseSchema)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific meeting by ID."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting with ID '{meeting_id}' not found.")
    return meeting

@router.get("/{meeting_id}/transcript")
def get_meeting_transcript(meeting_id: str, db: Session = Depends(get_db)):
    """Retrieve raw transcript text for a specific meeting."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting with ID '{meeting_id}' not found.")
    return {
        "id": meeting.id,
        "title": meeting.title,
        "transcript": meeting.transcript or ""
    }

@router.get("/{meeting_id}/audio")
def get_meeting_audio(meeting_id: str, db: Session = Depends(get_db)):
    """Stream audio recording file for a specific meeting."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting with ID '{meeting_id}' not found.")

    file_path = meeting.file_path
    if not file_path or not os.path.exists(file_path):
        settings = get_settings()
        ext = os.path.splitext(meeting.filename)[1].lower() if meeting.filename else ".mp3"
        alt_path = os.path.join(settings.UPLOAD_DIR, f"{meeting.id}{ext}")
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"Audio file not found for meeting '{meeting_id}'.")

    ext = os.path.splitext(file_path)[1].lower()
    media_type = MEDIA_TYPES.get(ext, "audio/mpeg")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=meeting.filename
    )

@router.delete("/{meeting_id}", status_code=status.HTTP_200_OK)
def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Delete a meeting record and its associated audio file."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting with ID '{meeting_id}' not found.")

    if meeting.file_path and os.path.exists(meeting.file_path):
        try:
            os.remove(meeting.file_path)
        except Exception:
            pass

    db.delete(meeting)
    db.commit()
    return {"message": f"Meeting '{meeting_id}' successfully deleted."}
