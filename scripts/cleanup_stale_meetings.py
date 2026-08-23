import requests

res = requests.get("http://127.0.0.1:8000/api/meetings").json()

# Group by transcript prefix
groups = {}
for m in res:
    t = (m.get("transcript") or "")[:50]
    key = t if t else "<EMPTY>"
    if key not in groups:
        groups[key] = []
    groups[key].append(m["id"][:8])

print(f"Total meetings: {len(res)}")
print(f"Distinct transcript prefixes: {len(groups)}")
print()
for prefix, ids in sorted(groups.items(), key=lambda x: -len(x[1])):
    print(f"Count={len(ids):<3}  Prefix: {prefix[:60]}")

# Identify test meeting IDs to keep
test_ids = set()
test_titles = ["Test - 01", "Test - 02", "Test - 03", "Test - 04", "Test - 05"]
for m in res:
    for tt in test_titles:
        if tt in m.get("title", ""):
            test_ids.add(m["id"])

print(f"\nTest meetings to KEEP: {len(test_ids)}")
stale = [m["id"] for m in res if m["id"] not in test_ids]
print(f"Stale meetings to DELETE: {len(stale)}")

# Delete stale meetings
for mid in stale:
    r = requests.delete(f"http://127.0.0.1:8000/api/meetings/{mid}")
    status = "OK" if r.status_code == 200 else f"FAIL({r.status_code})"
    print(f"  DELETE {mid[:8]}... {status}")

# Verify
remaining = requests.get("http://127.0.0.1:8000/api/meetings").json()
print(f"\nRemaining meetings: {len(remaining)}")
for m in remaining:
    t = (m.get("transcript") or "")[:60]
    print(f"  {m['id'][:8]}  {m['title']:<30}  Trans: {t}")
