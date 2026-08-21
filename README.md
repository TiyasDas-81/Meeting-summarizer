# 🎙️ AI Meeting Summarizer

A production-ready, executive AI Meeting Summarizer designed to transcribe audio recordings, generate concise meeting summaries, identify key decisions, and extract actionable tasks with assigned owners and deadlines.

---

## 📌 Problem Statement & Objective

In fast-paced organizations, valuable decisions and action items discussed during meetings are often forgotten or poorly documented. Manual meeting minutes are slow and error-prone.

The **AI Meeting Summarizer** solves this by automating the complete pipeline:
```
Audio File → ASR Transcription → Plain Text → LLM Analysis → Structured Insights → SQLite Database → Streamlit UI
```

---

## 🌟 Key Features

- **Multi-Format Audio Upload**: Supports `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`, `.aac` (up to 50MB).
- **Whisper ASR Integration**: Uses OpenAI Whisper API (`whisper_api`) or local Whisper (`whisper_local`) for speech-to-text.
- **LLM Executive Analysis**: Employs OpenAI GPT-4o or Google Gemini with prompt engineering to output structured JSON:
  - 📌 **Executive Summary**: Concise overview of meeting objectives and outcomes.
  - 🔑 **Key Discussion Points**: Bulleted discussion topics.
  - 🎯 **Decisions Made**: Explicitly agreed decisions.
  - ✅ **Action Items**: Structured tasks with `task`, `owner` (defaults to `"Unassigned"`), `deadline` (defaults to `"TBD"`), and `priority` (`High`/`Medium`/`Low`).
- **Long Transcript Chunking**: Handles long meeting transcripts by chunking text and synthesizing summaries before final analysis.
- **SQLite Database Persistence**: Stores meeting records, transcripts, summaries, and action item metadata.
- **Streamlit Executive Dashboard**: Interactive UI with audio playback, meeting history, status badges, and transcript downloads.
- **Offline/Mock Dev Mode**: Configurable mock mode for development and testing without API fees.
- **Comprehensive Automated Tests**: Pytest test suite covering API endpoints, DB operations, audio validation, chunking, and JSON parsing.

---

## 🏗️ Architecture & Data Flow

```
                                  +-----------------------+
                                  |   Audio File Upload   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  FastAPI Backend API  |
                                  | (/api/meetings/upload)|
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   Audio Validation    |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   Whisper ASR Engine  |
                                  | (whisper_local / API) |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  Full Text Transcript |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   LLM Summarizer      |
                                  | (JSON Schema Prompt)  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  SQLite DB & Storage  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |  Streamlit Dashboard  |
                                  +-----------------------+
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2
- **Frontend**: Streamlit
- **ASR (Speech-to-Text)**: Local OpenAI Whisper (`openai-whisper`) / OpenAI Whisper API (`whisper-1`)
- **LLM (Summarization)**: OpenAI GPT-4o-mini / Google Gemini 1.5 Flash
- **Database**: SQLite (`meetings.db`)
- **Testing**: Pytest, FastAPI TestClient

---

## 📂 Project Structure

```text
Meeting summarizer/
├── backend/
│   ├── api/
│   │   └── meetings.py        # FastAPI API routes (upload, list, get, delete)
│   ├── database/
│   │   └── db.py              # SQLAlchemy engine & session setup
│   ├── models/
│   │   └── meeting.py         # Meeting database model & JSON serializable properties
│   ├── schemas/
│   │   └── meeting.py         # Pydantic schemas & input validation
│   ├── services/
│   │   ├── transcription.py   # Audio validation & Whisper ASR service
│   │   ├── summarization.py   # LLM prompt, chunking & JSON extraction
│   │   └── meeting_processor.py # End-to-end processing pipeline orchestrator
│   ├── config.py              # Environment configuration loader
│   └── main.py                # FastAPI entry point & health endpoint
├── frontend/
│   └── app.py                 # Streamlit UI dashboard
├── tests/
│   ├── test_api.py            # API endpoint unit tests
│   ├── test_db.py             # Database CRUD tests
│   ├── test_summarization.py # LLM parser, schema & chunking tests
│   └── test_transcription.py  # Audio validation & ASR tests
├── uploads/                   # Audio upload storage directory
├── meetings.db                # SQLite database file
├── requirements.txt           # Python dependencies
├── .env                       # Active environment settings
├── .env.example               # Example configuration template
└── README.md                  # Project documentation
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10+ installed
- FFmpeg (included via project root or `imageio-ffmpeg`)

### 2. Installation
```powershell
cd "C:\Users\Asus\Desktop\Meeting summarizer"
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

Example `.env` configuration for **Local Whisper ASR + Real LLM**:
```env
# LLM API Settings (Options: openai, gemini, or mock)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini

# ASR Settings (Options: whisper_local, whisper_api, or mock)
ASR_PROVIDER=whisper_local
WHISPER_MODEL=tiny

# Database & Storage Settings
DATABASE_URL=sqlite:///./meetings.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
```

> 💡 **Note**: For local ASR (`ASR_PROVIDER=whisper_local`), no OpenAI API key is needed for speech recognition.

---

## 🏃 Running the Application

### 1. Start FastAPI Backend
```powershell
uvicorn backend.main:app --reload --port 8000
```
- API Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check Endpoint: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Start Streamlit Frontend
```powershell
streamlit run frontend/app.py
```
- Streamlit Dashboard URL: [http://localhost:8501](http://localhost:8501)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status & active configuration |
| `POST` | `/api/meetings/upload` | Upload audio recording & execute ASR + LLM processing |
| `GET` | `/api/meetings` | List all processed meetings (newest first) |
| `GET` | `/api/meetings/{id}` | Get full details & structured analysis for a meeting |
| `GET` | `/api/meetings/{id}/transcript` | Get raw transcript text |
| `DELETE` | `/api/meetings/{id}` | Delete meeting record & associated audio file |

---

## 🧪 Running Automated Tests

Run the full Pytest test suite:
```powershell
python -m pytest tests/ -v
```

Output:
```text
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_upload_meeting_success PASSED
tests/test_api.py::test_upload_unsupported_file_format PASSED
tests/test_api.py::test_upload_empty_file PASSED
tests/test_api.py::test_list_and_get_meeting PASSED
tests/test_db.py::test_meeting_orm_model_crud PASSED
tests/test_summarization.py::test_parse_json_from_llm_response_clean PASSED
tests/test_summarization.py::test_parse_json_from_llm_response_markdown_wrapper PASSED
tests/test_summarization.py::test_analyze_transcript_empty PASSED
tests/test_summarization.py::test_analyze_transcript_mock PASSED
tests/test_summarization.py::test_chunk_transcript PASSED
tests/test_summarization.py::test_action_item_schema_null_handling PASSED
tests/test_transcription.py::test_validate_audio_file_non_existent PASSED
tests/test_transcription.py::test_validate_audio_file_unsupported_format PASSED
tests/test_transcription.py::test_validate_audio_file_empty PASSED
tests/test_transcription.py::test_transcribe_audio_mock PASSED

============================= 16 passed in 1.12s ==============================
```

---

## 📝 Limitations

- Speaker Diarization (speaker identification like Speaker 1 / Speaker 2) is disabled by design.
- Audio file uploads are capped at 50MB by default (configurable in `.env`).

---

## 🔮 Future Enhancements

1. **Speaker Diarization**: Integrate PyAnnote.audio for speaker separation.
2. **Export Options**: Export meeting summary to PDF, Word, or Notion.
3. **Calendar & Email Integration**: Automatically send action items via Slack / Email webhooks.
