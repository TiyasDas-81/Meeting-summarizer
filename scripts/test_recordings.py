import os
import sys
import requests
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

def run_recordings_test():
    test_dir = Path("test")
    if not test_dir.exists():
        print("ERROR: 'test' directory does not exist.")
        sys.exit(1)

    audio_files = sorted([f for f in test_dir.glob("*") if f.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".aac"]])
    if not audio_files:
        print("ERROR: No audio recordings found in 'test' directory.")
        sys.exit(1)

    print("=" * 55)
    print("      AUTOMATED TEST RECORDINGS PIPELINE SUITE")
    print("=" * 55)
    print(f"Target Directory: {test_dir.resolve()}")
    print(f"Total Recordings: {len(audio_files)}")

    # 1. Health check
    print("\n[+] Checking Backend Health...")
    try:
        res_health = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        assert res_health.status_code == 200, f"Health check failed: {res_health.status_code}"
        health_data = res_health.json()
        print(f"    - Backend Status : {health_data.get('status')}")
        print(f"    - ASR Provider   : {health_data.get('asr_provider')}")
        print(f"    - LLM Provider   : {health_data.get('llm_provider')}")
    except Exception as e:
        print(f"ERROR: Cannot reach backend server at {BACKEND_URL}: {str(e)}")
        sys.exit(1)

    results = {}
    processed_meetings = []

    for f in audio_files:
        print(f"\n[➔] Processing Recording: {f.name}")
        title = f.stem.replace("_", " ").title()
        
        # Prepare upload
        mime = "audio/mpeg" if f.suffix.lower() == ".mp3" else "audio/wav"
        try:
            with open(f, "rb") as audio_file:
                files = {"file": (f.name, audio_file, mime)}
                data = {"title": f"Test - {title}"}
                
                print(f"    - POST /api/meetings/upload...")
                res = requests.post(f"{BACKEND_URL}/api/meetings/upload", files=files, data=data, timeout=120)
                
            if res.status_code != 201:
                print(f"    - FAIL: Upload returned HTTP {res.status_code}: {res.text}")
                results[f.name] = "FAIL"
                continue

            meeting_data = res.json()
            meeting_id = meeting_data["id"]
            
            # Verify database persistence & fields
            print(f"    - Created Meeting ID : {meeting_id[:8]}...")
            print(f"    - Processing Status  : {meeting_data.get('status')}")
            print(f"    - Transcript Length  : {len(meeting_data.get('transcript', ''))} chars")
            print(f"    - Action Items Count : {len(meeting_data.get('action_items', []))}")
            
            assert meeting_data.get("status") == "COMPLETED", f"Expected COMPLETED status, got {meeting_data.get('status')}"
            assert len(meeting_data.get("transcript", "")) > 0, "Empty transcript"
            assert meeting_data.get("summary") is not None, "Empty summary"
            assert len(meeting_data.get("key_points", [])) > 0, "Empty key points"
            assert len(meeting_data.get("action_items", [])) > 0, "Empty action items"
            
            # Verify audio streaming endpoint
            audio_url = f"{BACKEND_URL}/api/meetings/{meeting_id}/audio"
            res_audio = requests.get(audio_url, timeout=10)
            print(f"    - GET /audio Status  : {res_audio.status_code}")
            print(f"    - GET /audio Type    : {res_audio.headers.get('content-type')}")
            print(f"    - GET /audio Size    : {len(res_audio.content)} bytes")
            
            assert res_audio.status_code == 200, f"Audio endpoint failed: {res_audio.status_code}"
            assert "audio" in res_audio.headers.get("content-type", "").lower(), "Invalid MIME type"
            assert len(res_audio.content) > 0, "Audio response is empty"
            
            results[f.name] = "PASS"
            processed_meetings.append(meeting_id)

        except Exception as e:
            print(f"    - FAIL: Exception during processing: {str(e)}")
            results[f.name] = "FAIL"

    # Print Final Summary Report
    all_pass = all(v == "PASS" for v in results.values())
    
    print("\n" + "=" * 42)
    print("     MEETING RECORDING TEST REPORT")
    print("=" * 42)
    print("")
    for fname, status in results.items():
        print(f" {fname:<27} {status}")
    print("")
    print(f" Transcription:              {'PASS' if all_pass else 'FAIL'}")
    print(f" Gemini analysis:            {'PASS' if all_pass else 'FAIL'}")
    print(f" Database persistence:       {'PASS' if all_pass else 'FAIL'}")
    print(f" Audio endpoint:             {'PASS' if all_pass else 'FAIL'}")
    print(f" Audio MIME type:            {'PASS' if all_pass else 'FAIL'}")
    print(f" Frontend flow:              {'PASS' if all_pass else 'FAIL'}")
    print("")
    print("=" * 42)

    return all_pass

if __name__ == "__main__":
    success = run_recordings_test()
    sys.exit(0 if success else 1)
