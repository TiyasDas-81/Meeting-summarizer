import os
import sys
from typing import Dict, Any
from backend.config import get_settings

SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".aac"}

# Dynamically add imageio_ffmpeg binary folder or project root to PATH if available
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if os.path.exists(os.path.join(project_root, "ffmpeg.exe")):
    if project_root not in os.environ.get("PATH", ""):
        os.environ["PATH"] = project_root + os.pathsep + os.environ.get("PATH", "")

MOCK_TRANSCRIPT = (
    "Alex: Welcome everyone to the quarterly product roadmap sync. "
    "Today we need to finalize the mobile app launch schedule and assign key deliverables. "
    "Sarah: Based on our engineering Sprints, the iOS build will be ready for QA by next Wednesday, August 26th. "
    "David: Great. I will take responsibility for leading the QA testing team and submitting the app to the App Store. "
    "I'll need the final API documentation from Sarah by Monday. "
    "Sarah: Sound good, I will send over the API spec doc by Monday 5 PM. "
    "Alex: Excellent. We decided to launch the beta testing on September 1st. "
    "Let's make sure marketing materials are prepared by Priyanka before August 28th."
)

def validate_audio_file(file_path: str) -> bool:
    """Validates if file exists and has supported audio extension."""
    settings = get_settings()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported audio format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}")
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("Uploaded audio file is empty (0 bytes).")
        
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise ValueError(f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB.")
        
    return True

def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """
    Transcribes audio file using configured ASR provider (whisper_api, whisper_local, or mock).
    """
    validate_audio_file(file_path)
    settings = get_settings()
    provider = settings.ASR_PROVIDER.lower()

    if provider == "mock":
        return {
            "transcript": MOCK_TRANSCRIPT,
            "language": "english",
            "provider": "mock"
        }
    
    elif provider == "whisper_api":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in environment/configuration (.env). Set OPENAI_API_KEY=sk-... or ASR_PROVIDER=whisper_local / mock.")
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            with open(file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return {
                "transcript": response.text,
                "language": getattr(response, "language", "auto"),
                "provider": "whisper_api"
            }
        except Exception as e:
            raise RuntimeError(f"OpenAI Whisper API transcription failed: {str(e)}")

    elif provider == "whisper_local":
        try:
            import whisper
            model = whisper.load_model(settings.WHISPER_MODEL)
            result = model.transcribe(file_path)
            return {
                "transcript": result.get("text", "").strip(),
                "language": result.get("language", "auto"),
                "provider": "whisper_local"
            }
        except ImportError:
            raise RuntimeError("openai-whisper package is not installed. Run `pip install openai-whisper` or switch ASR_PROVIDER in .env.")
        except Exception as e:
            raise RuntimeError(f"Local Whisper transcription failed: {str(e)}")

    else:
        raise ValueError(f"Unknown ASR_PROVIDER '{provider}'. Options: whisper_api, whisper_local, mock.")
