"""
Bonus feature demo: request tracing + HPA auto-scaling.
Works against Docker Compose (localhost:8080) or K8s (any-node:30080).

Prereqs for HPA section (K8s only, one-time):
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    kubectl apply -f k8s/shortener-hpa.yaml

Usage:
    python demo_bonus.py # default: http://127.0.0.1:8080
    python demo_bonus.py http://<node-ip>:30080 # for K8s
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
USER = f"bonus_{tag}"
PASS = "bonuspass123"

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

print(f"\nURL Shortener Bonus Demo")
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

# setup
pause("Create a URL for tracing checks")
r = show(requests.post(f"{BASE}/", headers=headers, json={"value": "https://tracing-demo.example.com"}))
assert r.status_code == 201
trace_id = r.json()["id"]
print(f"  Short ID: {trace_id}")
confirm(f"Created tracing test URL /{trace_id}")

# request tracing
pause(
    f"Fetch /{trace_id} eight times to inspect tracing headers.\n"
    "Every shortener response should include:\n"
    "  X-Request-ID : unique ID per request\n"
    "  X-Served-By  : hostname of the instance that handled the request"
)
print("  8 sequential GETs:")
served_by = []
for i in range(1, 9):
    r = requests.get(f"{BASE}/{trace_id}", allow_redirects=False)
    assert r.status_code in (200, 301)
    x_served_by = r.headers.get("X-Served-By", "missing")
    x_request_id = r.headers.get("X-Request-ID", "missing")
    assert x_served_by != "missing", "Missing X-Served-By header"
    assert x_request_id != "missing", "Missing X-Request-ID header"
    served_by.append(x_served_by)
    print(f"    [{i}] status={r.status_code}  X-Served-By={x_served_by}  X-Request-ID={x_request_id[:16]}...")
unique_backends = sorted(set(served_by))
print(f"  Unique backends observed: {unique_backends}")
confirm(f"Observed tracing headers across {len(unique_backends)} backend(s)")

pause(
    f"Send a custom X-Request-ID header when fetching /{trace_id}.\n"
    "The service should echo it back unchanged."
)
r = show(
    requests.get(
        f"{BASE}/{trace_id}",
        headers={**headers, "X-Request-ID": "my-custom-trace-id-42"},
        allow_redirects=False,
    )
)
assert r.status_code in (200, 301)
echo = r.headers.get("X-Request-ID", "missing")
print(f"  Echoed X-Request-ID: {echo}")
assert echo == "my-custom-trace-id-42", f"Expected echo, got: {echo}"
confirm("Client-supplied request ID was preserved end-to-end")

# hpa auto-scaling
if "127.0.0.1" not in BASE and "localhost" not in BASE:
    pause(
        "HPA auto-scaling - in another terminal run:\n"
        "kubectl get hpa shortener-hpa -w\n"
        "Watch CPU and replicas, then press Enter to start generating load."
    )

    pause("Generate load with 60 POST /bulk requests")
    print("  Generating CPU load (60 x POST /bulk with 10 URLs each)...")
    bulk_payload = {"values": [f"https://load-test-{i}.example.com" for i in range(10)]}
    for i in range(60):
        r = requests.post(f"{BASE}/bulk", headers=headers, json=bulk_payload)
        assert r.status_code == 201, f"Bulk request failed at batch {i + 1}: {r.status_code}"
        if (i + 1) % 10 == 0:
            print(f"    batch {i + 1}/60 done")
    confirm("Load generation completed successfully")

    pause(
        "Check the HPA output in the other terminal.\n"
        "Replicas should have increased beyond 3 under load, then press Enter."
    )
    confirm("Observed HPA scale up under load")

    pause(
        "Wait about 60 seconds for load to drop.\n"
        "Press Enter once the HPA scales back down to 3 replicas."
    )
    confirm("Observed HPA scale back down to 3 replicas")
else:
    pause("HPA auto-scaling is Kubernetes-only. Press Enter to skip this section.")
    confirm("Skipped the HPA section for the local Docker Compose target")

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
    print("  BONUS DEMO COMPLETE - all steps passed")
else:
    print("  BONUS DEMO COMPLETE - some steps had server errors")
print(f"{'='*60}\n")
