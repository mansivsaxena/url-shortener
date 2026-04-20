#!/usr/bin/env python3
# Usage:
#   python test_bonus.py <base_url> burst   — fire 300 requests instantly, show 429s
#   python test_bonus.py <base_url> hpa     — sustained load to trigger HPA scaling

import sys, time, uuid, threading, requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

BASE = sys.argv[1].rstrip("/")
MODE = sys.argv[2] if len(sys.argv) > 2 else "hpa"

# register, login, create a URL
u, p = f"load_{uuid.uuid4().hex[:6]}", "loadtest123"
requests.post(f"{BASE}/auth/users", json={"username": u, "password": p})
token = requests.post(f"{BASE}/auth/users/login", json={"username": u, "password": p}).json()["token"]
hdrs  = {"Authorization": token}
sid   = requests.post(f"{BASE}/", json={"url": "https://example.com"}, headers=hdrs).json()["id"]
print(f"User: {u}  |  short code: /{sid}\n")

if MODE == "burst":
    # fire 300 requests concurrently
    print("Sending 300 requests at once to trigger rate limiting...\n")
    statuses = Counter()
    def req(_):
        r = requests.get(f"{BASE}/{sid}", allow_redirects=False, timeout=5)
        statuses[r.status_code] += 1
    with ThreadPoolExecutor(max_workers=100) as ex:
        list(ex.map(req, range(300)))
    print(f"301 (ok):          {statuses[301]}")
    print(f"429 (rate limited): {statuses[429]}")

else:  # hpa
    hits, rate_limited, lock = Counter(), Counter(), threading.Lock()

    def work():
        s, i = requests.Session(), 0
        while True:
            try:
                if i % 3 == 0:
                    r = s.post(f"{BASE}/", json={"url": "https://example.com"}, headers=hdrs, timeout=5)
                else:
                    r = s.get(f"{BASE}/{sid}", allow_redirects=False, timeout=5)
                pod = r.headers.get("X-Served-By")
                with lock:
                    if pod:
                        hits[pod] += 1
                    else:
                        rate_limited["429"] += 1
            except: pass
            i += 1

    print("Initiating sustained load using 40 threads. Watch pods in dashboard...\n")
    for _ in range(40):
        threading.Thread(target=work, daemon=True).start()

    try:
        while True:
            time.sleep(8)
            with lock:
                pods = dict(hits)
                blocked = rate_limited["429"]
            total = sum(pods.values())
            print(f"{total} reqs reached pods | {blocked} rate-limited (429) | {len(pods)} pod(s):")
            for pod, n in sorted(pods.items(), key=lambda x: -x[1]):
                print(f"  {pod}: {n}")
            print()
    except KeyboardInterrupt:
        print("Done.")
