import pytest
from backend.services.summarization import parse_json_from_llm_response, analyze_transcript
from backend.schemas.meeting import MeetingAnalysisSchema

def test_parse_json_from_llm_response_clean():
    raw = '{"summary": "Test summary", "key_points": ["p1"], "decisions": ["d1"], "action_items": []}'
    parsed = parse_json_from_llm_response(raw)
    assert parsed["summary"] == "Test summary"
    assert parsed["key_points"] == ["p1"]

def test_parse_json_from_llm_response_markdown_wrapper():
    raw = '```json\n{"summary": "Markdown wrapped", "key_points": [], "decisions": [], "action_items": []}\n```'
    parsed = parse_json_from_llm_response(raw)
    assert parsed["summary"] == "Markdown wrapped"

def test_analyze_transcript_empty():
    with pytest.raises(ValueError, match="empty transcript"):
        analyze_transcript("")

def test_analyze_transcript_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    analysis = analyze_transcript("Alice: Let's launch the product on Monday.")
    assert isinstance(analysis, MeetingAnalysisSchema)
    assert analysis.summary is not None
    assert isinstance(analysis.action_items, list)
    assert len(analysis.action_items) > 0
    assert hasattr(analysis.action_items[0], "task")
    assert hasattr(analysis.action_items[0], "owner")
    assert hasattr(analysis.action_items[0], "deadline")
    assert hasattr(analysis.action_items[0], "priority")

def test_chunk_transcript():
    from backend.services.summarization import chunk_transcript
    short_text = "Hello world. This is a short transcript."
    assert len(chunk_transcript(short_text, max_chars=100)) == 1

    long_text = "Sentence number. " * 1000
    chunks = chunk_transcript(long_text, max_chars=500)
    assert len(chunks) > 1

def test_action_item_schema_null_handling():
    from backend.schemas.meeting import ActionItemSchema
    item = ActionItemSchema(task="Draft report", owner=None, deadline="none", priority="High")
    assert item.owner == "Unassigned"
    assert item.deadline == "TBD"

