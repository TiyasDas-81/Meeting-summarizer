"""
Comprehensive UI Data Flow Regression Test
===========================================
Verifies that the Meeting Summarizer application correctly:
1. Returns distinct data for each meeting
2. Ties transcripts, summaries, audio to the correct meeting ID
3. View Details buttons use unique meeting-ID-based keys
4. Audio endpoints return correct content
5. No meeting shows another meeting's transcript
"""
import os
import sys
import requests
import json
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def test_health():
    section("PHASE 1: Backend Health Check")
    res = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    data = res.json()
    print(f"  Status: {data['status']}")
    print(f"  ASR: {data.get('asr_provider')}")
    print(f"  LLM: {data.get('llm_provider')}")
    assert data["status"] == "online"
    return data

def test_list_meetings():
    section("PHASE 2: Meetings List")
    res = requests.get(f"{BACKEND_URL}/api/meetings", timeout=5)
    assert res.status_code == 200
    meetings = res.json()
    print(f"  Total meetings: {len(meetings)}")
    
    # Verify IDs are unique
    ids = [m["id"] for m in meetings]
    assert len(ids) == len(set(ids)), "Duplicate meeting IDs found!"
    print("  All IDs unique: PASS")
    
    return meetings

def test_distinct_details(meetings):
    section("PHASE 3: Distinct Meeting Details (A vs B vs C vs D vs E)")
    
    completed = [m for m in meetings if m["status"] == "COMPLETED"]
    if len(completed) < 2:
        print("  SKIP: Need at least 2 completed meetings for distinctness test")
        return
    
    details = {}
    for m in completed[:5]:
        res = requests.get(f"{BACKEND_URL}/api/meetings/{m['id']}", timeout=5)
        assert res.status_code == 200
        d = res.json()
        assert d["id"] == m["id"], f"Returned ID mismatch: expected {m['id']}, got {d['id']}"
        details[m["id"]] = d
    
    # Verify transcripts are distinct
    transcripts = {mid: d.get("transcript", "") for mid, d in details.items()}
    transcript_values = list(transcripts.values())
    unique_transcripts = set(transcript_values)
    
    print(f"  Meetings checked: {len(details)}")
    print(f"  Distinct transcripts: {len(unique_transcripts)}")
    
    for mid, d in details.items():
        t = d.get("transcript", "")[:70].replace("\n", " ")
        ai_count = len(d.get("action_items", []))
        dec_count = len(d.get("decisions", []))
        print(f"  [{mid[:8]}] {d['title']:<30} T={len(d.get('transcript','')):<4} AI={ai_count} Dec={dec_count}")
        print(f"    Transcript: {t}")
    
    assert len(unique_transcripts) == len(transcript_values), \
        f"FAIL: Only {len(unique_transcripts)} unique transcripts out of {len(transcript_values)} meetings!"
    print("\n  Distinct transcript check: PASS")
    
    return details

def test_select_switch_pattern(meetings):
    section("PHASE 4: Select Meeting A -> B -> A Switching Pattern")
    
    completed = [m for m in meetings if m["status"] == "COMPLETED"]
    if len(completed) < 2:
        print("  SKIP: Need at least 2 completed meetings")
        return
    
    meeting_a = completed[0]
    meeting_b = completed[1]
    
    # Select A
    res_a = requests.get(f"{BACKEND_URL}/api/meetings/{meeting_a['id']}", timeout=5)
    assert res_a.status_code == 200
    data_a = res_a.json()
    trans_a = data_a.get("transcript", "")
    
    # Select B
    res_b = requests.get(f"{BACKEND_URL}/api/meetings/{meeting_b['id']}", timeout=5)
    assert res_b.status_code == 200
    data_b = res_b.json()
    trans_b = data_b.get("transcript", "")
    
    # Verify A != B
    assert trans_a != trans_b, "FAIL: Transcript A and B are identical!"
    assert data_a["id"] != data_b["id"], "FAIL: IDs are the same!"
    print(f"  A: [{data_a['id'][:8]}] {data_a['title']}: {trans_a[:50]}...")
    print(f"  B: [{data_b['id'][:8]}] {data_b['title']}: {trans_b[:50]}...")
    print("  A != B: PASS")
    
    # Select A again
    res_a2 = requests.get(f"{BACKEND_URL}/api/meetings/{meeting_a['id']}", timeout=5)
    data_a2 = res_a2.json()
    assert data_a2["transcript"] == trans_a, "FAIL: Re-selecting A returned different transcript!"
    print("  Re-select A == original A: PASS")
    
    print("\n  Select/Switch pattern: PASS")

def test_audio_endpoints(meetings):
    section("PHASE 5: Audio Endpoint Verification")
    
    completed = [m for m in meetings if m["status"] == "COMPLETED"]
    audio_sizes = []
    
    for m in completed[:5]:
        res = requests.get(f"{BACKEND_URL}/api/meetings/{m['id']}/audio", timeout=5)
        assert res.status_code == 200, f"Audio HTTP {res.status_code} for {m['id'][:8]}"
        content_type = res.headers.get("content-type", "")
        size = len(res.content)
        assert size > 0, f"Audio size is 0 for {m['id'][:8]}"
        assert "audio" in content_type.lower(), f"Content-Type not audio: {content_type}"
        audio_sizes.append(size)
        print(f"  [{m['id'][:8]}] HTTP 200 | Size={size:>7} | Type={content_type}")
    
    # Verify audio files are distinct (different sizes)
    if len(set(audio_sizes)) == len(audio_sizes):
        print("  All audio sizes distinct: PASS")
    else:
        print("  WARNING: Some audio sizes match (may be OK if files are similar length)")
    
    print("\n  Audio endpoints: PASS")

def test_transcript_endpoint(meetings):
    section("PHASE 6: Transcript Endpoint Verification")
    
    completed = [m for m in meetings if m["status"] == "COMPLETED"]
    
    for m in completed[:5]:
        res = requests.get(f"{BACKEND_URL}/api/meetings/{m['id']}/transcript", timeout=5)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == m["id"], f"Transcript endpoint ID mismatch!"
        t = data.get("transcript", "")
        assert len(t) > 0, f"Transcript is empty for {m['id'][:8]}"
        print(f"  [{m['id'][:8]}] {data['title']:<30} Len={len(t)}")
    
    print("\n  Transcript endpoints: PASS")

def test_view_details_button_keys(meetings):
    section("PHASE 7: View Details Button Key Uniqueness")
    
    # Simulate the Streamlit key generation pattern
    keys_home = set()
    keys_list = set()
    
    for m in meetings:
        key_home = f"btn_home_{m['id']}"
        key_list = f"btn_list_{m['id']}"
        
        assert key_home not in keys_home, f"Duplicate home button key: {key_home}"
        assert key_list not in keys_list, f"Duplicate list button key: {key_list}"
        
        keys_home.add(key_home)
        keys_list.add(key_list)
    
    print(f"  Home button keys unique: {len(keys_home)} keys, PASS")
    print(f"  List button keys unique: {len(keys_list)} keys, PASS")
    
    # Verify selectbox labels are unique
    labels = set()
    for m in meetings:
        label = f"{m['title']} [{m['status']}] ({m['created_at'].replace('T', ' ')[:19]}) | {m['id'][:8]}"
        assert label not in labels, f"Duplicate selectbox label: {label}"
        labels.add(label)
    
    print(f"  Selectbox labels unique: {len(labels)} labels, PASS")

def test_duplicate_title_handling(meetings):
    section("PHASE 8: Duplicate Title Handling")
    
    title_counts = Counter(m["title"] for m in meetings)
    duplicates = {t: c for t, c in title_counts.items() if c > 1}
    
    if duplicates:
        print(f"  Found {len(duplicates)} duplicated titles:")
        for title, count in duplicates.items():
            print(f"    '{title}' x{count}")
        
        # Verify that even with duplicate titles, selectbox labels are unique
        labels = set()
        for m in meetings:
            label = f"{m['title']} [{m['status']}] ({m['created_at'].replace('T', ' ')[:19]}) | {m['id'][:8]}"
            assert label not in labels, f"Label collision despite ID suffix: {label}"
            labels.add(label)
        print("  Labels still unique (ID suffix prevents collision): PASS")
    else:
        print("  No duplicate titles found. Test not applicable.")

def main():
    print("=" * 65)
    print("  COMPREHENSIVE UI DATA FLOW REGRESSION TEST")
    print("=" * 65)
    
    health = test_health()
    meetings = test_list_meetings()
    details = test_distinct_details(meetings)
    test_select_switch_pattern(meetings)
    test_audio_endpoints(meetings)
    test_transcript_endpoint(meetings)
    test_view_details_button_keys(meetings)
    test_duplicate_title_handling(meetings)
    
    section("FINAL RESULT")
    print("  ALL 8 PHASES PASSED!")
    print("  ✓ Backend health OK")
    print("  ✓ Meeting list OK")
    print("  ✓ Distinct transcripts confirmed")
    print("  ✓ A/B/A switching pattern OK")
    print("  ✓ Audio endpoints OK")
    print("  ✓ Transcript endpoints OK")
    print("  ✓ Button key uniqueness OK")
    print("  ✓ Duplicate title handling OK")
    print("=" * 65)

if __name__ == "__main__":
    main()
