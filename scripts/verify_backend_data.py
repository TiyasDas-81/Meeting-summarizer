import requests

BACKEND = "http://127.0.0.1:8000"
ids_prefix = ["a6f47537", "dac9f686", "cab76289", "7c45a999", "a2632871"]

res = requests.get(f"{BACKEND}/api/meetings").json()

for short_id in ids_prefix:
    match = [m for m in res if m["id"].startswith(short_id)]
    if match:
        m = match[0]
        full_id = m["id"]
        d = requests.get(f"{BACKEND}/api/meetings/{full_id}").json()
        trans = d.get("transcript", "")[:80].replace("\n", " ")
        title = d.get("title", "")[:30]
        trans_len = len(d.get("transcript", ""))
        ai = len(d.get("action_items", []))
        dec = len(d.get("decisions", []))
        print(f"ID={full_id[:8]}  Title={title:<30}  TransLen={trans_len:<5}  AI={ai}  Dec={dec}")
        print(f"  Transcript: {trans}")
        # Audio check
        aud = requests.get(f"{BACKEND}/api/meetings/{full_id}/audio")
        print(f"  Audio: HTTP {aud.status_code}  Size={len(aud.content)}  Content-Type={aud.headers.get('content-type','?')}")
        print()
