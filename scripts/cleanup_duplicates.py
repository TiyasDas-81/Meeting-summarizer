import requests

BACKEND = "http://127.0.0.1:8000"
res = requests.get(f"{BACKEND}/api/meetings").json()

# Keep only the first (newest) completed meeting per unique title
keep_ids = set()
seen_titles = set()
for m in res:
    title = m["title"]
    if title not in seen_titles and m["status"] == "COMPLETED":
        keep_ids.add(m["id"])
        seen_titles.add(title)

to_delete = [m["id"] for m in res if m["id"] not in keep_ids]
print(f"Keeping {len(keep_ids)} meetings, deleting {len(to_delete)} duplicates")

for mid in to_delete:
    r = requests.delete(f"{BACKEND}/api/meetings/{mid}")
    print(f"  DELETE {mid[:8]}... {'OK' if r.status_code == 200 else 'FAIL'}")

remaining = requests.get(f"{BACKEND}/api/meetings").json()
print(f"\nFinal meetings: {len(remaining)}")
for m in remaining:
    t = (m.get("transcript") or "")[:60]
    print(f"  {m['id'][:8]}  {m['title']:<30}  Status={m['status']:<10}  Trans: {t}")
