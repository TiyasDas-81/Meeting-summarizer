import streamlit as st
import requests
import os
import json
from datetime import datetime
from pathlib import Path

# Configure page layout and style
st.set_page_config(
    page_title="AI Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for executive design aesthetic
st.markdown("""
<style>
    /* Main layout typography & background */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Header card styling */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #38bdf8;
        font-weight: 700;
        margin-bottom: 0.25rem;
        font-size: 2.2rem;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1rem;
        margin: 0;
    }

    /* Priority badges */
    .priority-badge-high {
        background-color: #fef2f2;
        color: #dc2626;
        border: 1px solid #fca5a5;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .priority-badge-medium {
        background-color: #fffbebfb;
        color: #d97706;
        border: 1px solid #fcd34d;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .priority-badge-low {
        background-color: #f0fdf4;
        color: #16a34a;
        border: 1px solid #86efac;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Cards */
    .content-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Configuration & Backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".aac": "audio/aac",
}

def check_backend_health():
    try:
        res = requests.get(f"{BACKEND_URL}/api/health", timeout=3)
        if res.status_code == 200:
            return True, res.json()
    except Exception:
        pass
    return False, None

def fetch_meetings():
    try:
        res = requests.get(f"{BACKEND_URL}/api/meetings", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching meetings from backend: {str(e)}")
    return []

def fetch_meeting_detail(meeting_id):
    try:
        res = requests.get(f"{BACKEND_URL}/api/meetings/{meeting_id}", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching meeting details: {str(e)}")
    return None

def upload_and_process_meeting(uploaded_file, title):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    data = {"title": title} if title else {}
    try:
        res = requests.post(f"{BACKEND_URL}/api/meetings/upload", files=files, data=data, timeout=120)
        if res.status_code == 201:
            return res.json(), None
        else:
            try:
                err_detail = res.json().get("detail", res.text)
            except Exception:
                err_detail = res.text
            return None, f"Upload failed ({res.status_code}): {err_detail}"
    except Exception as e:
        return None, f"Connection error: {str(e)}"

def resolve_audio_path(meeting):
    file_path_str = meeting.get("file_path") or ""
    if file_path_str:
        p = Path(file_path_str)
        if not p.is_absolute():
            p = Path(os.getcwd()) / p
        if p.exists() and p.stat().st_size > 0:
            return p

    filename = meeting.get("filename") or ""
    if filename:
        p = Path(os.getcwd()) / "uploads" / filename
        if p.exists() and p.stat().st_size > 0:
            return p

    ext = Path(filename).suffix.lower() if filename else ".mp3"
    p = Path(os.getcwd()) / "uploads" / f"{meeting['id']}{ext}"
    if p.exists() and p.stat().st_size > 0:
        return p

    return None

# ====================================================
# SESSION STATE & NAVIGATION ARCHITECTURE
# ====================================================
# 1. State Initialization
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home & Upload"

if "selected_meeting_id" not in st.session_state:
    st.session_state.selected_meeting_id = None

# Sidebar setup
st.sidebar.markdown("### 🎙️ AI Meeting Summarizer")
st.sidebar.title("Navigation")

is_online, health_info = check_backend_health()
if is_online:
    st.sidebar.success(f"Backend Connected\nASR: {health_info.get('asr_provider', 'N/A')} | LLM: {health_info.get('llm_provider', 'N/A')}")
else:
    st.sidebar.error(f"Backend Offline ({BACKEND_URL})")
    st.sidebar.warning("Ensure FastAPI backend is running with `uvicorn backend.main:app --reload`")

PAGES = ["🏠 Home & Upload", "📋 Recent Meetings", "🔍 Meeting Details"]

current_nav_index = 0
if st.session_state.current_page in PAGES:
    current_nav_index = PAGES.index(st.session_state.current_page)

selected_radio_page = st.sidebar.radio(
    "Go to",
    PAGES,
    index=current_nav_index,
    key="sidebar_navigation_radio"
)

# Sync sidebar radio selection with current_page state
if selected_radio_page != st.session_state.current_page:
    st.session_state.current_page = selected_radio_page
    st.rerun()

def open_meeting_details(meeting_id):
    st.session_state.selected_meeting_id = meeting_id
    st.session_state.current_page = "🔍 Meeting Details"
    if "meeting_selectbox" in st.session_state:
        del st.session_state["meeting_selectbox"]
    st.rerun()

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>🎙️ AI Meeting Summarizer</h1>
    <p>Automated Audio Transcription & Executive Insight Extraction (Summary, Key Points, Decisions & Tasks)</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 1: HOME & UPLOAD
# ----------------------------------------------------
if st.session_state.current_page == "🏠 Home & Upload":
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📤 Upload Audio Recording")
        meeting_title = st.text_input("Meeting Title (Optional)", placeholder="e.g. Q3 Product Sprint Planning")

        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=["mp3", "wav", "m4a", "flac", "ogg", "webm", "aac"],
            help="Supported formats: WAV, MP3, M4A, FLAC, OGG, WEBM, AAC (Max 50MB)"
        )

        if uploaded_file is not None:
            st.info(f"📁 Selected file: **{uploaded_file.name}** ({uploaded_file.size / (1024*1024):.2f} MB)")

            if st.button("🚀 Process & Summarize Meeting", type="primary", use_container_width=True):
                if not is_online:
                    st.error("Cannot process audio because backend server is offline.")
                else:
                    progress_container = st.status("🔄 Processing Meeting Audio Pipeline...", expanded=True)

                    with progress_container:
                        st.write("📤 **STEP 1**: Uploading audio file... ⏳")
                        import time
                        time.sleep(0.5)
                        st.write("✓ **STEP 1**: Uploading audio — Complete")

                        st.write("🎙️ **STEP 2**: Transcribing with Whisper ASR... ⏳")
                        result, err = upload_and_process_meeting(uploaded_file, meeting_title)

                        if result:
                            st.write("✓ **STEP 2**: Transcribing with Whisper — Complete")
                            st.write("🧠 **STEP 3**: Analyzing transcript with LLM... ⏳")
                            time.sleep(0.3)
                            st.write("✓ **STEP 3**: Analyzing transcript with LLM — Complete")
                            st.write("📋 **STEP 4**: Extracting decisions and action items... ⏳")
                            time.sleep(0.3)
                            st.write("✓ **STEP 4**: Extracting decisions and action items — Complete")
                            st.write("💾 **STEP 5**: Saving meeting record... ⏳")
                            time.sleep(0.2)
                            st.write("✓ **STEP 5**: Saving meeting record — Complete")

                            progress_container.update(label="✅ Meeting Processing Complete!", state="complete", expanded=False)
                            st.success("✅ Meeting successfully processed!")
                            open_meeting_details(result["id"])
                        else:
                            progress_container.update(label="❌ Processing Failed", state="error", expanded=True)
                            st.error(f"❌ {err}")

    with col2:
        st.subheader("📊 Recent Summaries")
        meetings = fetch_meetings()
        if not meetings:
            st.info("No meetings processed yet. Upload your first audio recording!")
        else:
            for m in meetings[:4]:
                with st.container():
                    st.markdown(f"**{m['title']}**")
                    st.caption(f"📅 {m['created_at'][:10]} | ⚙️ Status: `{m['status']}`")
                    if m.get("summary"):
                        st.write(m['summary'][:120] + "...")
                    if st.button("View Details", key=f"btn_home_{m['id']}", type="primary"):
                        open_meeting_details(m['id'])
                    st.divider()

# ----------------------------------------------------
# TAB 2: RECENT MEETINGS
# ----------------------------------------------------
elif st.session_state.current_page == "📋 Recent Meetings":
    st.subheader("📚 All Processed Meetings")
    meetings = fetch_meetings()

    if not meetings:
        st.info("No meetings found in database.")
    else:
        search_query = st.text_input("🔍 Search by title or filename", placeholder="Type keywords...")
        if search_query:
            meetings = [m for m in meetings if search_query.lower() in m['title'].lower() or search_query.lower() in m['filename'].lower()]

        for m in meetings:
            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a:
                st.markdown(f"### {m['title']}")
                st.caption(f"File: `{m['filename']}` | Size: `{m['file_size'] / (1024*1024):.1f} MB` | ID: `{m['id'][:8]}...`")
            with col_b:
                status_color = "🟢" if m['status'] == "COMPLETED" else "🔴" if m['status'] == "FAILED" else "🟡"
                st.markdown(f"**Status:** {status_color} `{m['status']}`")
                st.caption(f"Uploaded: {m['created_at'].replace('T', ' ')[:16]}")
            with col_c:
                if st.button("View Meeting", key=f"btn_list_{m['id']}", type="primary"):
                    open_meeting_details(m['id'])
            st.divider()

# ----------------------------------------------------
# TAB 3: MEETING DETAILS
# ----------------------------------------------------
elif st.session_state.current_page == "🔍 Meeting Details":
    meetings = fetch_meetings()
    if not meetings:
        st.warning("No meetings available to display.")
    else:
        # Build label->id mapping and id->label reverse mapping
        label_to_id = {}
        id_to_label = {}
        for m in meetings:
            label = f"{m['title']} [{m['status']}] ({m['created_at'].replace('T', ' ')[:19]}) | {m['id'][:8]}"
            label_to_id[label] = m['id']
            id_to_label[m['id']] = label

        labels_list = list(label_to_id.keys())

        # Pre-set the selectbox session state to match selected_meeting_id
        # This MUST happen before the st.selectbox() call because Streamlit
        # ignores the `index` parameter when the key already exists in session_state.
        target_meeting_id = st.session_state.selected_meeting_id
        if target_meeting_id and target_meeting_id in id_to_label:
            st.session_state["meeting_selectbox"] = id_to_label[target_meeting_id]
        elif "meeting_selectbox" not in st.session_state or st.session_state["meeting_selectbox"] not in label_to_id:
            st.session_state["meeting_selectbox"] = labels_list[0]

        selected_label = st.selectbox(
            "Select Meeting",
            labels_list,
            key="meeting_selectbox"
        )

        # Derive the actual meeting ID from the selected label
        current_meeting_id = label_to_id[selected_label]

        # Sync back: if user changed selectbox manually, update selected_meeting_id
        if st.session_state.selected_meeting_id != current_meeting_id:
            st.session_state.selected_meeting_id = current_meeting_id

        meeting = fetch_meeting_detail(current_meeting_id)
        if meeting:
            # Metadata banner
            st.markdown(f"## 🎙️ {meeting['title']}")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Filename", meeting['filename'])
            m_col2.metric("Processing Status", meeting['status'])
            m_col3.metric("Action Items", len(meeting.get('action_items', [])))

            if meeting.get("error_message"):
                st.error(f"Processing Error: {meeting['error_message']}")

            # Audio Player Section
            st.subheader("🔊 Audio Player")

            audio_bytes = None
            audio_mime = "audio/mpeg"

            audio_url = f"{BACKEND_URL}/api/meetings/{meeting['id']}/audio"
            try:
                res = requests.get(audio_url, timeout=5)
                if res.status_code == 200 and len(res.content) > 0:
                    audio_bytes = res.content
                    c_type = res.headers.get("content-type", "")
                    if "wav" in c_type:
                        audio_mime = "audio/wav"
                    elif "mp4" in c_type or "m4a" in c_type:
                        audio_mime = "audio/mp4"
                    elif "ogg" in c_type:
                        audio_mime = "audio/ogg"
                    elif "webm" in c_type:
                        audio_mime = "audio/webm"
                    else:
                        audio_mime = "audio/mpeg"
            except Exception:
                pass

            if not audio_bytes:
                resolved_path = resolve_audio_path(meeting)
                if resolved_path:
                    try:
                        audio_bytes = resolved_path.read_bytes()
                        ext = resolved_path.suffix.lower()
                        audio_mime = MIME_TYPES.get(ext, "audio/mpeg")
                    except Exception:
                        pass

            if audio_bytes and len(audio_bytes) > 0:
                st.audio(audio_bytes, format=audio_mime)
            else:
                st.warning("⚠️ Audio recording file is not available for playback.")

            st.divider()

            # Structured Tabs
            tab_summary, tab_actions, tab_decisions, tab_transcript = st.tabs([
                "📌 Executive Summary & Key Points",
                "✅ Action Items / Tasks",
                "🎯 Key Decisions",
                "📄 Full Transcript"
            ])

            with tab_summary:
                st.subheader("Executive Summary")
                st.info(meeting.get("summary") or "No summary available.")

                st.subheader("Key Discussion Points")
                key_pts = meeting.get("key_points", [])
                if key_pts:
                    for pt in key_pts:
                        st.markdown(f"• {pt}")
                else:
                    st.write("No key points listed.")

            with tab_actions:
                st.subheader("Extracted Action Items")
                actions = meeting.get("action_items", [])
                if not actions:
                    st.info("No action items extracted from this meeting.")
                else:
                    for idx, item in enumerate(actions, 1):
                        p_level = item.get('priority', 'Medium').lower()
                        badge_class = f"priority-badge-{p_level}" if p_level in ['high', 'medium', 'low'] else "priority-badge-medium"

                        st.markdown(f"""
                        <div class="content-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin:0; color:#1e293b;">{idx}. {item.get('task')}</h4>
                                <span class="{badge_class}">{item.get('priority', 'Medium').upper()} PRIORITY</span>
                            </div>
                            <div style="margin-top: 0.5rem; color:#64748b; font-size: 0.9rem;">
                                👤 <strong>Owner:</strong> {item.get('owner', 'Unassigned')} &nbsp;&nbsp;|&nbsp;&nbsp;
                                📅 <strong>Deadline:</strong> {item.get('deadline', 'TBD')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            with tab_decisions:
                st.subheader("Key Decisions Made")
                decisions = meeting.get("decisions", [])
                if decisions:
                    for d in decisions:
                        st.success(f"✔ **{d}**")
                else:
                    st.write("No explicit decisions recorded.")

            with tab_transcript:
                st.subheader("Full Transcript")
                transcript_text = meeting.get("transcript") or ""
                if transcript_text:
                    st.text_area("Transcript Text", value=transcript_text, height=350)

                    st.download_button(
                        label="📥 Download Transcript (.txt)",
                        data=transcript_text,
                        file_name=f"{meeting['title']}_transcript.txt",
                        mime="text/plain"
                    )
                else:
                    st.warning("Transcript is empty or not available.")
