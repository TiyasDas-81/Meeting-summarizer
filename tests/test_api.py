import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import get_settings

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "asr_provider" in data
    assert "llm_provider" in data

def test_upload_meeting_success(tmp_path):
    sample_file = tmp_path / "test_meeting.wav"
    sample_file.write_bytes(b"RIFF dummy audio content 1234567890")

    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("test_meeting.wav", f, "audio/wav")},
            data={"title": "Test Executive Sync"}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Executive Sync"
    assert data["status"] == "COMPLETED"
    assert data["summary"] is not None
    assert len(data["action_items"]) > 0

def test_upload_unsupported_file_format(tmp_path):
    sample_file = tmp_path / "bad_file.txt"
    sample_file.write_bytes(b"This is a text document")

    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("bad_file.txt", f, "text/plain")}
        )

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

def test_upload_empty_file(tmp_path):
    empty_file = tmp_path / "empty.wav"
    empty_file.write_bytes(b"")

    with open(empty_file, "rb") as f:
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("empty.wav", f, "audio/wav")}
        )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_list_and_get_meeting(tmp_path):
    sample_file = tmp_path / "meeting2.mp3"
    sample_file.write_bytes(b"RIFF dummy mp3 content")

    with open(sample_file, "rb") as f:
        res_create = client.post(
            "/api/meetings/upload",
            files={"file": ("meeting2.mp3", f, "audio/mp3")},
            data={"title": "Sprint Retrospective"}
        )
    meeting_id = res_create.json()["id"]

    res_list = client.get("/api/meetings")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    res_get = client.get(f"/api/meetings/{meeting_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == meeting_id

    res_trans = client.get(f"/api/meetings/{meeting_id}/transcript")
    assert res_trans.status_code == 200
    assert "transcript" in res_trans.json()

def test_get_meeting_audio(tmp_path):
    sample_file = tmp_path / "meeting_audio_test.mp3"
    sample_file.write_bytes(b"ID3 dummy mp3 audio content")

    with open(sample_file, "rb") as f:
        res_create = client.post(
            "/api/meetings/upload",
            files={"file": ("meeting_audio_test.mp3", f, "audio/mp3")},
            data={"title": "Audio Stream Test"}
        )
    meeting_id = res_create.json()["id"]

    res_audio = client.get(f"/api/meetings/{meeting_id}/audio")
    assert res_audio.status_code == 200
    assert "audio" in res_audio.headers.get("content-type", "").lower()
