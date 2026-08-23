import requests

BACKEND = "http://127.0.0.1:8000"
res = requests.get(f"{BACKEND}/api/meetings").json()

test_prefix = "Test - "
for m in res:
    title = m["title"]
    mid = m["id"]
    if not title.startswith(test_prefix):
        r = requests.delete(f"{BACKEND}/api/meetings/{mid}")
        status = "OK" if r.status_code == 200 else "FAIL"
        print(f"DELETE {mid[:8]}  {title:<30}  {status}")

remaining = requests.get(f"{BACKEND}/api/meetings").json()
print(f"\nRemaining: {len(remaining)}")
for m in remaining:
    print(f"  {m['id'][:8]}  {m['title']}")
