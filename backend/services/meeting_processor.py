import logging
from sqlalchemy.orm import Session
from backend.models.meeting import Meeting
from backend.services.transcription import transcribe_audio
from backend.services.summarization import analyze_transcript

logger = logging.getLogger(__name__)

def process_meeting(meeting_id: str, db: Session) -> Meeting:
    """
    Executes end-to-end meeting processing pipeline: Audio -> ASR -> LLM -> DB.
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise ValueError(f"Meeting with ID '{meeting_id}' not found.")

    try:
        # Step 1: Update status to PROCESSING
        meeting.status = "PROCESSING"
        db.commit()
        db.refresh(meeting)

        # Step 2: Audio Transcription (Whisper ASR)
        asr_result = transcribe_audio(meeting.file_path)
        meeting.transcript = asr_result.get("transcript", "")
        
        # Step 3: LLM Analysis (Summary, Key Points, Decisions, Action Items)
        analysis = analyze_transcript(meeting.transcript)
        
        meeting.summary = analysis.summary
        meeting.key_points = analysis.key_points
        meeting.decisions = analysis.decisions
        meeting.action_items = [item.model_dump() for item in analysis.action_items]
        
        meeting.status = "COMPLETED"
        meeting.error_message = None

    except Exception as e:
        logger.error(f"Processing failed for meeting {meeting_id}: {str(e)}", exc_info=True)
        meeting.status = "FAILED"
        meeting.error_message = str(e)
    
    finally:
        db.commit()
        db.refresh(meeting)

    return meeting
