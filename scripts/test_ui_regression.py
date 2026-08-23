import os
import sys
import requests
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

def test_distinct_meetings_regression():
    print("=" * 65)
    print("   MEETING DATAFLOW & DISTINCT TRANSCRIPT REGRESSION TEST")
    print("=" * 65)

    # 1. Fetch meetings list
    res_list = requests.get(f"{BACKEND_URL}/api/meetings", timeout=5)
    assert res_list.status_code == 200, f"Failed to list meetings: {res_list.status_code}"
    meetings = res_list.json()
    
    # Filter completed test meetings
    test_titles = ["Test - 01 Product Sprint", "Test - 02 Team Standup", "Test - 03 Client Meeting", "Test - 04 Project Risk", "Test - 05 Retrospective"]
    target_meetings = []
    
    for title in test_titles:
        matched = [m for m in meetings if title.lower() in m.get('title', '').lower() and m.get('status') == "COMPLETED"]
        if matched:
            target_meetings.append(matched[0])

    print(f"\n[+] Found {len(target_meetings)} target test meetings out of {len(meetings)} total database meetings.")
    assert len(target_meetings) == 5, f"Expected 5 test meetings, found {len(target_meetings)}"

    meeting_ids = []
    transcripts = []
    summaries = []
    audio_sizes = []

    print("\n" + "-" * 65)
    print(f"| {'Title':<25} | {'Meeting ID':<10} | {'Trans Chars':<11} | {'Audio Size':<10} |")
    print("-" * 65)

    for m in target_meetings:
        m_id = m['id']
        res_detail = requests.get(f"{BACKEND_URL}/api/meetings/{m_id}", timeout=5)
        assert res_detail.status_code == 200
        detail = res_detail.json()

        m_trans = detail.get('transcript', '').strip()
        m_sum = detail.get('summary', '').strip()
        
        # Audio check
        res_audio = requests.get(f"{BACKEND_URL}/api/meetings/{m_id}/audio", timeout=5)
        assert res_audio.status_code == 200
        assert "audio" in res_audio.headers.get("content-type", "").lower()
        a_bytes = len(res_audio.content)
        assert a_bytes > 0

        meeting_ids.append(m_id)
        transcripts.append(m_trans)
        summaries.append(m_sum)
        audio_sizes.append(a_bytes)

        print(f"| {detail.get('title'):<25} | {m_id[:8]:<10} | {len(m_trans):<11} | {a_bytes:<10} |")

    print("-" * 65)

    # Assertions for Distinctness
    print("\n[+] Verifying Dataflow & Distinctness...")
    assert len(set(meeting_ids)) == 5, "Meeting IDs are not distinct!"
    assert len(set(transcripts)) == 5, "Transcripts are NOT distinct! Identical transcript detected!"
    assert len(set(audio_sizes)) == 5, "Audio file sizes are NOT distinct!"
    
    for i, t in enumerate(transcripts):
        print(f"    - Meeting {i+1} [{target_meetings[i]['title']}]: {t[:60]}...")

    print("\n" + "=" * 65)
    print("   ALL REGRESSION CHECKS PASSED: 5 DISTINCT TRANSCRIPTIONS & AUDIOS!")
    print("=" * 65)

if __name__ == "__main__":
    test_distinct_meetings_regression()
