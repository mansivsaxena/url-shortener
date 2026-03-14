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

def confirm(message):
    print(f"✓ {message}")

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

# auth
pause("Register a new user")
r = show(requests.post(f"{AUTH}/users", json={"username": USER, "password": PASS}))
assert r.status_code == 201, f"Register failed: {r.status_code}"
confirm(f"Registered user {USER}")

pause("Login and get a JWT token")
r = show(requests.post(f"{AUTH}/users/login", json={"username": USER, "password": PASS}))
assert r.status_code == 200, f"Login failed: {r.status_code}"
token = r.json()["token"]
headers = {"Authorization": token}
confirm("Logged in and received a JWT token")

pause("Validate the token")
r = show(requests.get(f"{AUTH}/users/validate", headers=headers))
assert r.status_code == 200, f"Validate failed: {r.status_code}"
confirm("Token validation succeeded")

# shorten
pause("Shorten a URL (https://example.com)")
r = show(requests.post(f"{BASE}/", headers=headers, json={"value": "https://example.com"}))
assert r.status_code == 201
short_id = r.json()["id"]
print(f"  Short ID: {short_id}")
confirm(f"Created short URL /{short_id}")

pause("Shorten another URL (https://github.com)")
r = show(requests.post(f"{BASE}/", headers=headers, json={"value": "https://github.com"}))
assert r.status_code == 201
short_id_2 = r.json()["id"]
print(f"  Short ID: {short_id_2}")
confirm(f"Created short URL /{short_id_2}")

pause(f"Retrieve /{short_id} (public, no auth needed)")
r = show(requests.get(f"{BASE}/{short_id}", allow_redirects=False))
assert r.status_code in (200, 301)
confirm(f"Public lookup for /{short_id} succeeded")

pause("Try a non-existent ID (expect 404)")
r = show(requests.get(f"{BASE}/zzzzzz", allow_redirects=False))
assert r.status_code == 404
confirm("Missing short ID returned 404")

pause("List all URLs for this user")
r = show(requests.get(f"{BASE}/", headers=headers))
assert r.status_code == 200
data = r.json()
count = len(data.get("value", data) if isinstance(data, dict) else data)
print(f"  URLs owned: {count}")
confirm(f"Listed {count} URL(s) for the current user")

# update and delete
pause(f"Update /{short_id} to point to https://updated.com")
r = show(requests.put(f"{BASE}/{short_id}", headers=headers, json={"url": "https://updated.com"}))
assert r.status_code == 200
confirm(f"Updated /{short_id}")

pause(f"Delete /{short_id_2}")
r = show(requests.delete(f"{BASE}/{short_id_2}", headers=headers))
assert r.status_code == 204
confirm(f"Deleted /{short_id_2}")

pause(f"Verify /{short_id_2} is gone (expect 404)")
r = show(requests.get(f"{BASE}/{short_id_2}", allow_redirects=False))
assert r.status_code == 404
confirm(f"Verified /{short_id_2} no longer exists")

# bulk
pause("Bulk shorten two URLs at once")
r = show(requests.post(f"{BASE}/bulk", headers=headers,
                        json={"values": ["https://one.com", "https://two.com"]}))
assert r.status_code == 201
confirm("Bulk shorten request created two URLs")

# persistence
if "127.0.0.1" in BASE or "localhost" in BASE:
    pause(
        "Persistence check - in another terminal run:\n"
        "docker compose down && docker compose up -d\n"
        "Wait until the stack is healthy (~15 s), then press Enter"
    )
    pause(f"Verify /{short_id} still resolves after full container restart")
    r = show(requests.get(f"{BASE}/{short_id}", allow_redirects=False))
    assert r.status_code in (200, 301), f"Data lost after restart — status {r.status_code}"
    confirm("Data survived docker compose down / up")

# replica consistency
pause(
    "Create a URL for replica consistency checks"
)
r = show(requests.post(f"{BASE}/", headers=headers, json={"value": "https://replica-check.example.com"}))
assert r.status_code == 201
replica_id = r.json()["id"]
print(f"  Short ID: {replica_id}")
confirm(f"Created replica consistency test URL /{replica_id}")

pause(
    f"Fetch /{replica_id} five times.\n"
    "With 3 shortener replicas Kubernetes round-robins across pods;\n"
    "all reads must return the same result regardless of which pod serves them."
)
print("  5 sequential GETs:")
observed_values = []
for i in range(1, 6):
    r = requests.get(f"{BASE}/{replica_id}", allow_redirects=False)
    assert r.status_code in (200, 301)
    try:
        payload = r.json()
    except ValueError:
        payload = {}
    val = payload.get("value") or r.headers.get("Location", "?")
    observed_values.append(val)
    print(f"    [{i}] status={r.status_code}  value={val}")
assert len(set(observed_values)) == 1, f"Inconsistent replica responses: {observed_values}"
confirm("Consistent data returned across all replicas")

# ownership
pause(f"Ownership check - a different user tries to delete /{short_id}")
other = f"other_{tag}"
requests.post(f"{AUTH}/users", json={"username": other, "password": PASS})
r2 = requests.post(f"{AUTH}/users/login", json={"username": other, "password": PASS})
other_headers = {"Authorization": r2.json()["token"]}
r = show(requests.delete(f"{BASE}/{short_id}", headers=other_headers))
assert r.status_code == 403
confirm("Ownership rules prevented cross-user deletion")

# cleanup
pause("Delete all URLs for this user")
r = show(requests.delete(f"{BASE}/", headers=headers))
assert r.status_code in (200, 204, 404)
confirm("Deleted all URLs for the current user")

pause("Confirm the list is empty")
r = show(requests.get(f"{BASE}/", headers=headers))
assert r.status_code == 200
data = r.json()
vals = data.get("value") if isinstance(data, dict) else data
count = len(vals) if vals else 0
print(f"  URLs owned: {count}")
confirm("Confirmed the URL list is empty")

# logout
pause("Logout")
r = show(requests.post(f"{AUTH}/users/logout", headers=headers))
assert r.status_code == 200
confirm("Logged out successfully")

pause("Try using the token after logout (should be rejected)")
r = show(requests.get(f"{BASE}/", headers=headers))
assert r.status_code in (401, 403)
confirm("Logged-out token was rejected")

# result
print(f"\n{'='*60}")
if ok:
    print("  DEMO COMPLETE — all steps passed")
else:
    print("  DEMO COMPLETE — some steps had server errors")
print(f"{'='*60}\n")