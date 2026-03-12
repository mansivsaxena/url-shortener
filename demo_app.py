"""
Quick demo of the URL shortener stack.
Works against Docker Compose (localhost:8080) or K8s (any-node:30080).

Usage:
    python demo_app.py # default: http://127.0.0.1:8080
    python demo_app.py http://<node-ip>:30080 # for K8s
"""

import sys
import subprocess
import random
import string
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8080"
AUTH = f"{BASE}/auth"

# if targeting localhost, make sure docker compose is up
if "127.0.0.1" in BASE or "localhost" in BASE:
    try:
        requests.get(f"{BASE}/healthz", timeout=2)
    except Exception:
        print("Stack not running, starting docker compose...")
        subprocess.run(["docker", "compose", "up", "--build", "-d"], check=True)
        import time
        for i in range(30):
            try:
                requests.get(f"{BASE}/healthz", timeout=2)
                break
            except Exception:
                time.sleep(1)
        else:
            sys.exit("Stack failed to start")

# using random username
tag = "".join(random.choices(string.ascii_lowercase, k=5))
USER = f"demo_{tag}"
PASS = "demopass123"

ok = True

def pause(label):
    input(f"\n[Enter] {label}")
    print()

def show(r):
    global ok
    status = r.status_code
    body = r.text[:300]
    print(f"  Status: {status}")
    print(f"  Body:   {body}")
    if status >= 500:
        ok = False
    return r

print(f"\nURL Shortener Demo")
print(f"Target: {BASE}")
print(f"User:   {USER}")

# ── Auth ──────────────────────────────────────────────────────

pause("Register a new user")
r = show(requests.post(f"{AUTH}/users", json={"username": USER, "password": PASS}))
assert r.status_code == 201, f"Register failed: {r.status_code}"

pause("Login and get a JWT token")
r = show(requests.post(f"{AUTH}/users/login", json={"username": USER, "password": PASS}))
assert r.status_code == 200, f"Login failed: {r.status_code}"
token = r.json()["token"]
headers = {"Authorization": token}

pause("Validate the token")
r = show(requests.get(f"{AUTH}/users/validate", headers=headers))
assert r.status_code == 200, f"Validate failed: {r.status_code}"

# ── Shorten ───────────────────────────────────────────────────

pause("Shorten a URL (https://example.com)")
r = show(requests.post(f"{BASE}/", headers=headers, json={"value": "https://example.com"}))
assert r.status_code == 201
short_id = r.json()["id"]
print(f"  Short ID: {short_id}")

pause("Shorten another URL (https://github.com)")
r = show(requests.post(f"{BASE}/", headers=headers, json={"value": "https://github.com"}))
assert r.status_code == 201
short_id_2 = r.json()["id"]
print(f"  Short ID: {short_id_2}")

pause(f"Retrieve /{short_id} (public, no auth needed)")
r = show(requests.get(f"{BASE}/{short_id}", allow_redirects=False))
assert r.status_code in (200, 301)

pause("Try a non-existent ID (expect 404)")
r = show(requests.get(f"{BASE}/zzzzzz", allow_redirects=False))
assert r.status_code == 404

pause("List all URLs for this user")
r = show(requests.get(f"{BASE}/", headers=headers))
assert r.status_code == 200
data = r.json()
count = len(data.get("value", data) if isinstance(data, dict) else data)
print(f"  URLs owned: {count}")

# ── Update & Delete ───────────────────────────────────────────

pause(f"Update /{short_id} to point to https://updated.com")
r = show(requests.put(f"{BASE}/{short_id}", headers=headers, json={"url": "https://updated.com"}))
assert r.status_code == 200

pause(f"Delete /{short_id_2}")
r = show(requests.delete(f"{BASE}/{short_id_2}", headers=headers))
assert r.status_code == 204

pause(f"Verify /{short_id_2} is gone (expect 404)")
r = show(requests.get(f"{BASE}/{short_id_2}", allow_redirects=False))
assert r.status_code == 404

# ── Bulk ──────────────────────────────────────────────────────

pause("Bulk shorten two URLs at once")
r = show(requests.post(f"{BASE}/bulk", headers=headers,
                        json={"values": ["https://one.com", "https://two.com"]}))
assert r.status_code == 201

# ── Ownership ─────────────────────────────────────────────────

pause(f"Ownership check — a different user tries to delete /{short_id}")
other = f"other_{tag}"
requests.post(f"{AUTH}/users", json={"username": other, "password": PASS})
r2 = requests.post(f"{AUTH}/users/login", json={"username": other, "password": PASS})
other_headers = {"Authorization": r2.json()["token"]}
r = show(requests.delete(f"{BASE}/{short_id}", headers=other_headers))
assert r.status_code == 403

# ── Cleanup ───────────────────────────────────────────────────

pause("Delete all URLs for this user")
r = show(requests.delete(f"{BASE}/", headers=headers))
assert r.status_code in (200, 204, 404)

pause("Confirm the list is empty")
r = show(requests.get(f"{BASE}/", headers=headers))
assert r.status_code == 200
data = r.json()
vals = data.get("value") if isinstance(data, dict) else data
count = len(vals) if vals else 0
print(f"  URLs owned: {count}")

# ── Logout ────────────────────────────────────────────────────

pause("Logout")
r = show(requests.post(f"{AUTH}/users/logout", headers=headers))
assert r.status_code == 200

pause("Try using the token after logout (should be rejected)")
r = show(requests.get(f"{BASE}/", headers=headers))
assert r.status_code in (401, 403)

# ── Result ────────────────────────────────────────────────────

print(f"\n{'='*60}")
if ok:
    print("  DEMO COMPLETE — all steps passed")
else:
    print("  DEMO COMPLETE — some steps had server errors")
print(f"{'='*60}\n")
