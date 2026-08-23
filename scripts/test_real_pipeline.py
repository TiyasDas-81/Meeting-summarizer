import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import get_settings
from backend.services.transcription import transcribe_audio, validate_audio_file
from backend.services.summarization import analyze_transcript
from backend.database.db import SessionLocal, engine, Base
from backend.models.meeting import Meeting

def run_pipeline_test():
    print("=" * 45)
    print("   MEETING SUMMARIZER PIPELINE TEST")
    print("=" * 45)

    # 1. Configuration check
    settings = get_settings()
    # If ASR is set to mock, force local whisper for real audio test if available
    asr_provider = settings.ASR_PROVIDER
    if asr_provider.lower() == "mock":
        os.environ["ASR_PROVIDER"] = "whisper_local"
        asr_provider = "whisper_local (forced for real audio test)"

    print(f"[1] Configuration: PASS")
    print(f"    - ASR Provider : {asr_provider}")
    print(f"    - LLM Provider : {settings.LLM_PROVIDER}")
    print(f"    - Database URL : {settings.DATABASE_URL}")

    # 2. Audio file check
    audio_path = os.path.join(project_root, "uploads", "real_meeting_recording.mp3")
    if not os.path.exists(audio_path):
        # Fallback to any audio file in uploads
        uploads_dir = os.path.join(project_root, "uploads")
        audio_files = [f for f in os.listdir(uploads_dir) if f.endswith((".mp3", ".wav", ".m4a"))]
        if audio_files:
            audio_path = os.path.join(uploads_dir, audio_files[0])

    try:
        validate_audio_file(audio_path)
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"[2] Audio file check: PASS ({os.path.basename(audio_path)} - {file_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[2] Audio file check: FAIL - {str(e)}")
        sys.exit(1)

    # 3. ASR Transcription
    print("[3] Running ASR Speech-to-Text...")
    try:
        asr_result = transcribe_audio(audio_path)
        transcript = asr_result.get("transcript", "").strip()
        print(f"[3] ASR Execution: PASS (Provider: {asr_result.get('provider')})")
        print(f"[4] Transcript generated: PASS")
        print(f"    - Transcript Length: {len(transcript)} characters")
        print(f"    - Preview: {transcript[:180]}...")
    except Exception as e:
        print(f"[3] ASR Execution: FAIL - {str(e)}")
        sys.exit(1)

    # 4. LLM Summarization Analysis
    print("[5] Running LLM Structured Analysis...")
    try:
        analysis = analyze_transcript(transcript)
        print(f"[5] LLM Analysis: PASS")
        print(f"[6] Executive Summary: PASS")
        print(f"    - Summary: {analysis.summary}")
        print(f"[7] Key points: {len(analysis.key_points)} extracted")
        for pt in analysis.key_points:
            print(f"      - {pt}")
        print(f"[8] Decisions: {len(analysis.decisions)} extracted")
        for dec in analysis.decisions:
            print(f"      + {dec}")
        print(f"[9] Action items: {len(analysis.action_items)} extracted")
        for idx, item in enumerate(analysis.action_items, 1):
            print(f"      {idx}. {item.task} | Owner: {item.owner} | Deadline: {item.deadline} | Priority: {item.priority}")
    except Exception as e:
        print(f"[5] LLM Analysis: FAIL - {str(e)}")
        sys.exit(1)

    # 5. Database Persistence Check
    print("[10] Testing SQLite Database Persistence...")
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        
        meeting = Meeting(
            title="Pipeline Diagnostic Run",
            filename=os.path.basename(audio_path),
            file_path=audio_path,
            file_size=os.path.getsize(audio_path),
            status="COMPLETED",
            transcript=transcript,
            summary=analysis.summary,
            key_points=analysis.key_points,
            decisions=analysis.decisions,
            action_items=[item.model_dump() for item in analysis.action_items]
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        # Retrieve meeting to confirm round-trip persistence
        fetched = db.query(Meeting).filter(Meeting.id == meeting.id).first()
        if not fetched or len(fetched.action_items) != len(analysis.action_items):
            raise RuntimeError("Database record retrieved did not match saved object.")
        
        print(f"[10] Database Persistence: PASS (Meeting ID: {fetched.id})")
        db.close()
    except Exception as e:
        print(f"[10] Database Persistence: FAIL - {str(e)}")
        sys.exit(1)

    print("=" * 45)
    print("   FINAL RESULT: PASS")
    print("=" * 45)

if __name__ == "__main__":
    run_pipeline_test()
