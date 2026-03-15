#!/usr/bin/env python3
# Usage: python demo_load.py <base_url> [threads]
# Example: python demo_load.py http://<node-ip>:30080 40

import sys, time, uuid, threading, requests
from collections import Counter

BASE    = sys.argv[1].rstrip("/")
THREADS = int(sys.argv[2]) if len(sys.argv) > 2 else 40

u, p = f"load_{uuid.uuid4().hex[:6]}", "loadtest123"
requests.post(f"{BASE}/auth/users", json={"username": u, "password": p})
token = requests.post(f"{BASE}/auth/users/login", json={"username": u, "password": p}).json()["token"]
hdrs  = {"Authorization": token}
sid   = requests.post(f"{BASE}/", json={"url": "https://example.com"}, headers=hdrs).json()["id"]

print(f"Hammering /{sid} with {THREADS} threads. Ctrl+C to stop.\n")

hits, lock = Counter(), threading.Lock()

def work():
    s = requests.Session()
    i = 0
    while True:
        try:
            # every 3rd request is a POST (auth call + DB write) for extra CPU pressure
            if i % 3 == 0:
                r = s.post(f"{BASE}/", json={"url": "https://example.com"}, headers=hdrs, timeout=5)
            else:
                r = s.get(f"{BASE}/{sid}", allow_redirects=False, timeout=5)
            pod = r.headers.get("X-Served-By", "?")
            with lock: hits[pod] += 1
        except: pass
        i += 1

for _ in range(THREADS):
    threading.Thread(target=work, daemon=True).start()

try:
    while True:
        time.sleep(8)
        with lock:
            total = sum(hits.values())
            pods  = dict(hits)
        print(f"{total} reqs | {len(pods)} pod(s):")
        for pod, n in sorted(pods.items(), key=lambda x: -x[1]):
            print(f"  {pod}: {n}")
        print()
except KeyboardInterrupt:
    print("Done.")
