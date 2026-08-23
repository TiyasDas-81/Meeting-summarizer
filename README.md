# 🎙️ AI Meeting Summarizer

An automated AI application designed to transcribe meeting audio recordings, generate concise executive summaries, extract key discussion points and decisions, and organize actionable tasks with assigned owners, deadlines, and priorities.

---

## 📌 Problem Statement

In modern team workflows, key decisions and action items discussed during meetings are often lost or buried in lengthy audio recordings. Manual meeting documentation is time-consuming, inconsistent, and prone to human error.

- **Lengthy Recordings**: Reviewing hours of recorded calls to find a single detail is inefficient.
- **Manual Minute Taking**: Note-takers often miss critical discussion context while typing.
- **Lost Action Items**: Tasks discussed informally often lack clear ownership or deadlines.
- **Lack of Structured Follow-up**: Unstructured meeting notes make tracking project progress difficult.

### How AI Meeting Summarizer Solves This

**AI Meeting Summarizer** converts unstructured audio conversations into structured, actionable intelligence automatically. By pairing local speech-to-text transcription with structured LLM analysis, the system transforms meeting audio into executive summaries, key decisions, and concrete task tables available instantly via an interactive web dashboard.

---

## 🎯 Objective

> Transcribe meeting audio and transform the conversation into structured, action-oriented insights.

The platform processes raw audio files to generate:
- **Full Text Transcripts** with high-accuracy speech recognition.
- **Executive Summaries** summarizing the meeting's objective and core outcomes.
- **Key Discussion Points** categorized logically.
- **Key Decisions** agreed upon by participants.
- **Action Items** with explicit tasks, owners, deadlines, and priority rankings.

---

## 🏗️ Architecture & Data Pipeline

```text
Audio Recording (.mp3, .wav, .m4a, etc.)
                   │
                   ▼
       FastAPI Backend API Layer
                   │
                   ▼
  Whisper ASR (Local / OpenAI API / Mock)
                   │
                   ▼
          Full Text Transcript
                   │
                   ▼
 LLM Analysis Engine (Gemini / OpenAI / Mock)
                   │
                   ▼
┌──────────────────────────────────────────┐
│ Executive Summary                        │
│ Key Discussion Points                    │
│ Key Decisions                            │
│ Action Items (Task, Owner, Deadline, Prio)│
└──────────────────────────────────────────┘
                   │
                   ▼
         SQLite Database Storage
                   │
                   ▼
   Streamlit Executive Web Dashboard
```

### Component Overview

1. **FastAPI Backend (`backend/`)**: Serves RESTful API endpoints for audio ingestion, asynchronous pipeline processing, meeting retrieval, audio streaming, and record deletion.
2. **Speech-to-Text Engine (`backend/services/transcription.py`)**: Uses OpenAI Whisper running locally or via API to convert speech audio into clear text transcripts.
3. **LLM Summarization Engine (`backend/services/summarization.py`)**: Prompts Google Gemini or OpenAI LLMs with strict JSON schema instructions to extract structured insights and handle long transcript chunking.
4. **Database & Storage (`backend/models/meeting.py`, `backend/database/db.py`)**: Persists meeting records, transcripts, summaries, and action item metadata cleanly in SQLite.
5. **Streamlit Web Dashboard (`frontend/app.py`)**: Offers an executive UI to upload recordings, inspect recent summaries, listen to audio playback, and download transcripts.

---

## 🤖 AI Stack & Models

- **Speech-to-Text (ASR)**:
  - Primary Local Provider: **OpenAI Whisper** (`whisper_local` using model size `tiny`/`base`).
  - API Fallback Provider: **OpenAI Whisper API** (`whisper_api` using model `whisper-1`).
  - Development Provider: **Mock ASR** (`mock` for zero-cost offline development).
- **Large Language Model (LLM)**:
  - Primary Gemini Model: **Google Gemini** (`gemini-3.6-flash`).
  - Alternative Provider: **OpenAI** (`gpt-4o-mini`).
  - Offline Provider: **Mock LLM** (`mock` for rule-based testing without API keys).

---

## 🌟 Key Features

- 📤 **Multi-Format Audio Upload**: Supports `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.webm`, and `.aac` files (up to 50MB).
- 🎙️ **Local Speech Recognition**: High-accuracy local speech-to-text using OpenAI Whisper without third-party API dependencies for audio processing.
- 🧠 **Structured Executive Insights**: Generates structured summaries, discussion points, team decisions, and task lists.
- 👤 **Owner & Deadline Detection**: Extracts task assignees and target deadlines directly from conversational context.
- 🏷️ **Priority Classification**: Categorizes tasks into `High`, `Medium`, or `Low` priority.
- 📜 **Long Transcript Chunking**: Automatically segments long transcripts (>12,000 characters) into overlapping chunks to preserve context across extended meetings.
- 🔊 **Audio Recording Playback**: Stream and replay stored meeting audio directly from the dashboard via a dedicated media streaming endpoint (`/api/meetings/{id}/audio`).
- 🔍 **Meeting History & Search**: Browse, filter, and inspect past meetings by keyword or date.
- 📥 **Transcript Export**: Download complete meeting transcripts as plain text files (`.txt`).
- 🛡️ **Structured Output Validation**: Enforces JSON schema compliance and validates LLM responses via Pydantic models.
- ⚙️ **Configurable Pipeline**: Easily toggle between Gemini, OpenAI, or offline Mock modes using `.env` settings.

---

## 🔄 Demo Workflow

1. **Upload Audio**: User uploads a meeting recording (`.mp3`, `.wav`, etc.) via the Streamlit interface.
2. **Validation & Ingestion**: FastAPI validates file extension, file size, and stores the audio binary in `./uploads`.
3. **Speech Transcription**: Whisper ASR transcribes the audio into a complete plain text transcript.
4. **LLM Insight Analysis**: The transcript is passed to Google Gemini with strict prompt constraints.
5. **JSON Schema Extraction**: Summary, key points, decisions, and action items are structured and validated.
6. **Database Persistence**: The meeting record and JSON payloads are saved to SQLite (`meetings.db`).
7. **Executive Dashboard**: User explores executive summaries, decisions, and action item cards.
8. **Audio Replay & Download**: User listens to the original audio recording or downloads the raw transcript.

---

## 📋 Action Item Structure

Extracts concrete, actionable tasks from meeting conversations into structured records:

*(Example Representation)*

| Task Description | Owner | Deadline | Priority |
| :--- | :--- | :--- | :--- |
| Finalize API integration documentation | Sarah | Monday 5 PM | High |
| Lead QA testing and handle App Store submission | David | Wednesday, Aug 26 | High |
| Prepare marketing materials for beta launch | Priyanka | August 28th | Medium |
| Follow up on cloud infrastructure migration | Unassigned | TBD | Low |

> 💡 **Note**: The system avoids inventing missing owners or deadlines. If a task owner or deadline is not explicitly stated in the conversation, standard fallback values (`Unassigned` / `TBD`) are applied automatically.

---

## 🛠️ Tech Stack

| Component Layer | Technology Used |
| :--- | :--- |
| **Frontend UI** | Streamlit |
| **Backend Framework** | FastAPI (Uvicorn, ASGI) |
| **ASR (Speech-to-Text)** | OpenAI Whisper (Local / API) |
| **LLM (Summarization)** | Google Gemini (`gemini-3.6-flash`) / OpenAI (`gpt-4o-mini`) |
| **Database** | SQLite & SQLAlchemy ORM |
| **Data Validation** | Pydantic v2 |
| **Language & Testing** | Python 3.10+, Pytest |

---

## 📂 Project Structure

```text
Meeting-summarizer/
├── backend/
│   ├── api/
│   │   └── meetings.py            # FastAPI REST endpoints (upload, list, detail, audio, delete)
│   ├── database/
│   │   └── db.py                  # SQLAlchemy engine & session manager
│   ├── models/
│   │   └── meeting.py             # Meeting database model & JSON properties
│   ├── schemas/
│   │   └── meeting.py             # Pydantic schemas & output validation
│   ├── services/
│   │   ├── transcription.py       # Audio validation & Whisper ASR service
│   │   ├── summarization.py       # LLM prompt, chunking & JSON parser
│   │   └── meeting_processor.py   # End-to-end processing pipeline orchestrator
│   ├── config.py                  # Pydantic settings & environment configuration
│   └── main.py                    # FastAPI app entry point & health check endpoint
├── frontend/
│   └── app.py                     # Streamlit executive dashboard UI
├── tests/
│   ├── test_api.py                # REST API integration tests
│   ├── test_db.py                 # SQLite Database CRUD unit tests
│   ├── test_summarization.py     # LLM JSON parser, fallback & chunking tests
│   └── test_transcription.py      # Audio format validation & ASR tests
├── scripts/
│   ├── test_recordings.py         # End-to-end recording pipeline verification suite
│   ├── test_ui_flow.py            # UI data-flow & state regression verification suite
│   └── cleanup_duplicates.py      # Utility maintenance scripts
├── uploads/                       # Storage for uploaded audio files (Git ignored)
├── test/                          # Sample test recordings directory (Git ignored)
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git exclusion rules
├── requirements.txt               # Dependencies list
└── README.md                      # Project documentation
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```powershell
git clone https://github.com/TiyasDas-81/Meeting-summarizer.git
cd Meeting-summarizer
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to create your active `.env` file:
```powershell
cp .env.example .env
```

Edit `.env` to configure your API keys and providers:
```env
# LLM Settings (Options: gemini, openai, or mock)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# Optional OpenAI LLM configuration
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini

# ASR Settings (Options: whisper_local, whisper_api, or mock)
ASR_PROVIDER=whisper_local
WHISPER_MODEL=base

# Storage & Database
DATABASE_URL=sqlite:///./meetings.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
```

> 🔒 **Security Notice**: Never commit `.env` or real API keys to version control. `.env` is listed in `.gitignore`.

---

## 🏃 Running the Application

### 1. Start Backend Server (FastAPI)
Open a terminal in the project root and run:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Start Frontend Interface (Streamlit)
Open a second terminal in the project root and run:
```powershell
python -m streamlit run frontend/app.py --server.port 8501
```
- **Streamlit Web Application**: [http://localhost:8501](http://localhost:8501)

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check endpoint returning active ASR and LLM configurations |
| `POST` | `/api/meetings/upload` | Upload audio file, execute Whisper ASR and LLM analysis, save to DB |
| `GET` | `/api/meetings` | List all processed meetings (newest first) |
| `GET` | `/api/meetings/{id}` | Retrieve complete details, summary, key points, and action items |
| `GET` | `/api/meetings/{id}/transcript` | Retrieve raw transcript text for a meeting |
| `GET` | `/api/meetings/{id}/audio` | Stream original audio recording file |
| `DELETE` | `/api/meetings/{id}` | Delete meeting record and its underlying audio file |

---

## 🔊 Audio Playback Integration

The application includes native audio streaming capability. Stored audio recordings can be played back directly from the Streamlit frontend.

- **Endpoint**: `GET /api/meetings/{meeting_id}/audio`
- **Behavior**: Streams the original binary file with the correct MIME header (`audio/mpeg`, `audio/wav`, `audio/mp4`, etc.), allowing inline playback without loading entire audio files into client memory.

---

## 🧪 Testing & Verification

The repository features comprehensive automated unit, integration, and data-flow verification suites.

### Run Pytest Suite
```powershell
python -m pytest tests/ -v
```
*(Runs 17 unit and API integration tests covering endpoints, database CRUD, JSON parsing, and audio validation.)*

### Run Recording Pipeline Test Suite
```powershell
python scripts/test_recordings.py
```
*(Verifies end-to-end processing across audio samples and checks database integrity.)*

### Run UI Data-Flow Regression Test
```powershell
python scripts/test_ui_flow.py
```
*(Executes an 8-phase automated verification of UI state switching, audio playback endpoints, and component keys.)*

---

## 🖼️ Application Preview

> Screenshots can be added here for the final submission.

---

## 🧠 LLM Prompt & Anti-Hallucination Design

The summarization service uses structured prompt constraints to maintain data integrity:

1. **Strict JSON Output**: The model is mandated to return valid JSON conforming to the `MeetingAnalysisSchema`.
2. **Decision vs. Discussion Separation**: Explicitly agreed decisions are separated from general conversational topics.
3. **No Hallucination Rules**: If an owner or deadline is not mentioned in the transcript, the model is strictly instructed to fill `"Unassigned"` or `"TBD"` rather than inferring imaginary people or dates.
4. **Markdown Tag Cleaners & Regex Fallback**: A resilient parser strips markdown syntax wrappers (```json) and uses regex fallbacks if LLM responses contain surrounding prose.

---

## ⚠️ Current Limitations

- **Processing Speed**: Local Whisper model execution depends on client CPU/GPU capabilities.
- **API Key Requirement**: Production LLM features require a valid Google Gemini or OpenAI API key.
- **Deployment Scope**: Designed primarily as a local/demo application.
- **Concurrency**: SQLite database is optimized for local single-node deployments.

---

## 🔮 Future Enhancements

- 👥 **Speaker Diarization**: Integrate `pyannote.audio` for automatic speaker identification (e.g., Speaker A / Speaker B).
- 🌐 **Multilingual Support**: Support multi-language meeting transcription and auto-translation.
- 📅 **Calendar & Workspace Integration**: Auto-sync action items to Google Calendar, Jira, or Trello.
- 📧 **Automated Notifications**: Send meeting digests via Email or Slack webhooks upon completion.
- 🔒 **User Authentication**: Multi-tenant access controls and secure user logins.
- ☁️ **Cloud Storage Integration**: Store meeting recordings in AWS S3 or Google Cloud Storage.

---

## 🏆 Why This Project?

**AI Meeting Summarizer** solves a universal workplace problem: turning unstructured meeting audio into structured accountability. By unifying local speech recognition, structured LLM extraction, resilient data storage, and a user-friendly executive dashboard, it turns hours of meeting audio into actionable productivity in seconds.
