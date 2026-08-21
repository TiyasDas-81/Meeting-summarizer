import os
import pytest
from backend.services.transcription import validate_audio_file, transcribe_audio

def test_validate_audio_file_non_existent():
    with pytest.raises(FileNotFoundError):
        validate_audio_file("non_existent_audio_file.wav")

def test_validate_audio_file_unsupported_format(tmp_path):
    bad_file = tmp_path / "document.pdf"
    bad_file.write_bytes(b"%PDF-1.4 dummy pdf content")
    with pytest.raises(ValueError, match="Unsupported audio format"):
        validate_audio_file(str(bad_file))

def test_validate_audio_file_empty(tmp_path):
    empty_file = tmp_path / "empty.wav"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        validate_audio_file(str(empty_file))

def test_transcribe_audio_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "mock")
    sample_file = tmp_path / "sample.wav"
    sample_file.write_bytes(b"RIFF sample audio bytes")
    
    result = transcribe_audio(str(sample_file))
    assert "transcript" in result
    assert len(result["transcript"]) > 0
    assert result["provider"] == "mock"
