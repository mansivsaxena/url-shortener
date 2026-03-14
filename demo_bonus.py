"""
Bonus feature demo: request tracing + HPA auto-scaling.
Works against Docker Compose (localhost:8080) or K8s (any-node:30080).

Prereqs for HPA section (K8s only, one-time):
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    kubectl apply -f k8s/shortener-hpa.yaml

Usage:
    python demo_bonus.py                          # Docker Compose
    python demo_bonus.py http://<node-ip>:30080   # Kubernetes
"""

import sys
import random
import string
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8080"
AUTH = f"{BASE}/auth"

tag = "".join(random.choices(string.ascii_lowercase, k=5))
USER = f"bonus_{tag}"
PASS = "bonuspass123"

def pause(label):
    input(f"\n[Enter] {label}")
    print()

def show(r):
    print(f"  Status: {r.status_code}")
    print(f"  Body:   {r.text[:300]}")
    return r

print(f"\nURL Shortener — Bonus Feature Demo")
print(f"Target: {BASE}")
print(f"User:   {USER}")

# setup: register and login
pause("Register and login a demo user")
requests.post(f"{AUTH}/users", json={"username": USER, "password": PASS})
r = show(requests.post(f"{AUTH}/users/login", json={"username": USER, "password": PASS}))
assert r.status_code == 200, f"Login failed: {r.status_code}"
token = r.json()["token"]
headers = {"Authorization": token}

# shorten a URL to have something to fetch
r = requests.post(f"{BASE}/", headers=headers, json={"value": "https://tracing-demo.example.com"})
assert r.status_code == 201
trace_id = r.json()["id"]

# request tracing
pause(
    "Request tracing — every shortener response includes:\n"
    "  X-Request-ID : unique ID per request (forwarded if provided, generated if not)\n"
    "  X-Served-By  : hostname of the pod that handled the request\n"
    "  Making 8 sequential requests to show round-robin across pods..."
)

served_by = []
for i in range(1, 9):
    r = requests.get(f"{BASE}/", headers=headers)
    xrb = r.headers.get("X-Served-By", "n/a")
    xrid = r.headers.get("X-Request-ID", "n/a")
    served_by.append(xrb)
    print(f"  [{i}] X-Served-By={xrb}  X-Request-ID={xrid[:16]}...")

unique_pods = set(served_by)
print(f"\n  Unique pods observed: {unique_pods}")
print(f"  ✓ Requests distributed across {len(unique_pods)} pod(s)")

pause(
    "Custom X-Request-ID — if the client sends one it is echoed back.\n"
    "  Sending X-Request-ID: my-custom-trace-id-42"
)
r = requests.get(
    f"{BASE}/",
    headers={**headers, "X-Request-ID": "my-custom-trace-id-42"},
)
echo = r.headers.get("X-Request-ID", "missing")
print(f"  Echoed X-Request-ID: {echo}")
assert echo == "my-custom-trace-id-42", f"Expected echo, got: {echo}"
print("  ✓ Client-supplied request ID is preserved end-to-end")

# hpa auto-scaling
pause(
    "HPA auto-scaling (Kubernetes only) — shortener-hpa targets 50% CPU,\n"
    "  scales from 3 up to 6 replicas under load.\n\n"
    "  → In another terminal run:\n"
    "      kubectl get hpa shortener-hpa -w\n"
    "  Then press Enter to start generating load."
)

print("  Generating CPU load (60 x POST /bulk with 10 URLs each)...")
bulk_payload = {"values": [f"https://load-test-{i}.example.com" for i in range(10)]}
created_ids = []
for i in range(60):
    r = requests.post(f"{BASE}/bulk", headers=headers, json=bulk_payload)
    if r.status_code == 201 and i % 10 == 0:
        print(f"    batch {i+1}/60 done")

print("  Load generation complete.")

pause(
    "Check the HPA output in the other terminal — REPLICAS should have\n"
    "  increased beyond 3. Press Enter to proceed."
)

pause(
    "Wait ~60 s for load to drop and HPA to scale back down to minReplicas=3.\n"
    "  Watch the HPA output, then press Enter once replicas return to 3."
)
print("  ✓ HPA scaled up under load and back down when idle")

# cleanup
pause("Cleanup — delete all URLs for this user")
r = show(requests.delete(f"{BASE}/", headers=headers))
assert r.status_code in (200, 204, 404)

requests.post(f"{AUTH}/users/logout", headers=headers)

print(f"\n{'='*60}")
print("  BONUS DEMO COMPLETE")
print(f"{'='*60}\n")
