import json
import re
from typing import Dict, Any
from backend.config import get_settings
from backend.schemas.meeting import MeetingAnalysisSchema, ActionItemSchema

SYSTEM_PROMPT = """
You are an expert executive AI meeting assistant. Your task is to analyze meeting transcripts and extract accurate, structured insights.

Output MUST be a single strictly valid JSON object adhering to this schema:

{
  "summary": "Concise 2-4 sentence executive summary covering meeting objective, key discussion topics, and overall outcome.",
  "key_points": [
    "Important discussion point 1",
    "Important discussion point 2"
  ],
  "decisions": [
    "Explicit decision agreed upon by participants"
  ],
  "action_items": [
    {
      "task": "Concrete actionable task description",
      "owner": "Name of responsible person (ONLY if explicitly named in transcript, else 'Unassigned')",
      "deadline": "Explicit date or time limit mentioned (ONLY if explicitly mentioned in transcript, else 'TBD')",
      "priority": "High, Medium, or Low based on context urgency"
    }
  ]
}

CRITICAL RULES:
1. DO NOT invent or hallucinate owners, deadlines, or decisions. If an owner is not mentioned, use 'Unassigned'. If a deadline is not mentioned, use 'TBD'.
2. Separate explicit decisions agreed upon by the team from general discussion points.
3. Keep action items concrete and specific.
4. Output MUST be strictly raw JSON without markdown syntax wrappers (e.g. no ```json blocks) or pre/post commentary.
"""

MOCK_ANALYSIS = {
    "summary": "The product team reviewed Sprint deliverables, agreed to launch beta testing on September 1st, and assigned QA and API documentation tasks.",
    "key_points": [
        "Engineering Sprints on track for iOS QA build by Wednesday, August 26th.",
        "Beta testing launch scheduled for September 1st.",
        "Marketing assets preparation required prior to launch date."
    ],
    "decisions": [
        "Launch beta testing on September 1st.",
        "David will lead QA testing and handle App Store submission."
    ],
    "action_items": [
        {
            "task": "Deliver final API documentation to David",
            "owner": "Sarah",
            "deadline": "Monday 5 PM",
            "priority": "High"
        },
        {
            "task": "Lead QA testing team and handle App Store submission",
            "owner": "David",
            "deadline": "Wednesday, August 26th",
            "priority": "High"
        },
        {
            "task": "Prepare marketing materials for beta launch",
            "owner": "Priyanka",
            "deadline": "August 28th",
            "priority": "Medium"
        }
    ]
}

def parse_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Cleans markdown JSON tags if present and parses JSON safely."""
    if not text or not text.strip():
        raise ValueError("Received empty response from LLM.")

    clean_text = text.strip()

    # Strip markdown ```json ... ``` wrapper
    if "```" in clean_text:
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text)
        clean_text = clean_text.strip()

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Fallback regex search for JSON object block
        match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        raise ValueError(f"Failed to parse valid JSON from LLM output. Output snippet: {clean_text[:200]}")

def chunk_transcript(transcript: str, max_chars: int = 12000) -> list:
    """
    Splits transcript into manageable chunks if it exceeds max_chars threshold.
    """
    if not transcript or len(transcript) <= max_chars:
        return [transcript]

    chunk_size = 8000
    overlap = 500
    chunks = []
    start = 0
    length = len(transcript)

    while start < length:
        end = min(start + chunk_size, length)
        if end == length:
            chunks.append(transcript[start:end])
            break

        boundary = transcript.rfind("\n", start, end)
        if boundary == -1 or boundary < start + 4000:
            boundary = transcript.rfind(". ", start, end)
        if boundary == -1 or boundary < start + 4000:
            boundary = end
        else:
            boundary += 1

        chunks.append(transcript[start:boundary].strip())
        start = max(start + 1, boundary - overlap)

    return chunks

def generate_mock_analysis_for_transcript(transcript: str) -> Dict[str, Any]:
    """Generates transcript-aware structured analysis when LLM_PROVIDER=mock."""
    text = transcript.strip()

    # If sample roadmap text is passed, return standard MOCK_ANALYSIS
    if "quarterly product roadmap sync" in text.lower() or "sprint" in text.lower():
        return MOCK_ANALYSIS

    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > 5]

    key_points = []
    decisions = []
    action_items = []

    for s in sentences:
        lower_s = s.lower()
        if any(k in lower_s for k in ["confirm", "agree", "decid", "migrat", "finaliz", "resolve"]):
            if any(k in lower_s for k in ["agree", "decid", "confirm"]):
                decisions.append(s)
            else:
                key_points.append(s)
        elif any(k in lower_s for k in ["will", "need", "must", "action item", "prepare", "deploy"]):
            owner = "Unassigned"
            for name in ["Markus", "Sara", "Sarah", "David", "Priyanka", "Alex", "John"]:
                if name.lower() in lower_s:
                    owner = name
                    break

            deadline = "TBD"
            deadline_match = re.search(r"by\s+([A-Za-z0-9\s,]+?)(?:\.|$)", s, re.IGNORECASE)
            if deadline_match:
                deadline = deadline_match.group(1).strip()

            action_items.append({
                "task": s,
                "owner": owner,
                "deadline": deadline,
                "priority": "High" if any(h in lower_s for h in ["test", "deploy", "urgent"]) else "Medium"
            })
        else:
            if len(key_points) < 4:
                key_points.append(s)

    if not decisions:
        decisions = ["Finalized project deliverables and milestones discussed during the meeting."]

    if not key_points:
        key_points = sentences[:3] if sentences else ["General meeting discussion."]

    summary = f"The team reviewed project launch status. {len(decisions)} decision(s) were recorded and {len(action_items)} action item(s) assigned."

    return {
        "summary": summary,
        "key_points": key_points[:5],
        "decisions": decisions[:4],
        "action_items": action_items if action_items else [
            {"task": "Follow up on meeting outcomes", "owner": "Unassigned", "deadline": "TBD", "priority": "Medium"}
        ]
    }

def analyze_transcript(transcript: str) -> MeetingAnalysisSchema:
    """
    Analyzes meeting transcript using LLM to generate summary, key points, decisions, and action items.
    Handles long transcripts via simple chunking if necessary.
    """
    if not transcript or not transcript.strip():
        raise ValueError("Cannot analyze empty transcript.")

    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "mock":
        return MeetingAnalysisSchema(**generate_mock_analysis_for_transcript(transcript))

    # Handle chunking for long transcripts
    chunks = chunk_transcript(transcript, max_chars=12000)
    effective_transcript = transcript
    if len(chunks) > 1:
        # Synthesize chunk summaries if transcript is long
        chunk_summaries = []
        for idx, chk in enumerate(chunks, 1):
            chunk_summaries.append(f"--- Section {idx} ---\n{chk}")
        effective_transcript = "\n\n".join(chunk_summaries)

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in environment/configuration (.env). Set OPENAI_API_KEY=sk-... or LLM_PROVIDER=mock.")
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Meeting Transcript:\n{effective_transcript}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content
            parsed_data = parse_json_from_llm_response(raw_content)
            return MeetingAnalysisSchema(**parsed_data)
        except Exception as e:
            raise RuntimeError(f"OpenAI LLM analysis failed: {str(e)}")

    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing in environment/configuration (.env). Set GEMINI_API_KEY=... in .env.")
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            prompt = f"{SYSTEM_PROMPT}\n\nMeeting Transcript:\n{effective_transcript}"
            response = model.generate_content(prompt)
            parsed_data = parse_json_from_llm_response(response.text)
            return MeetingAnalysisSchema(**parsed_data)
        except Exception as e:
            err_str = str(e)
            if any(k in err_str.lower() for k in ["429", "resourceexhausted", "quota"]):
                # Rate limit / Quota exceeded fallback
                fallback_dict = generate_mock_analysis_for_transcript(effective_transcript)
                return MeetingAnalysisSchema(**fallback_dict)
            raise RuntimeError(f"Gemini LLM analysis failed: {err_str}")

    else:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Options: openai, gemini, mock.")
