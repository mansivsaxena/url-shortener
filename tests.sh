#!/usr/bin/env bash
set -e

source .venv/bin/activate

python run.py & SERVER_PID=$!
sleep 0.6

cleanup() {
  kill "$SERVER_PID" 2>/dev/null
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Marking tests ==="
python test_1_marking_mk2.py
MARK_EXIT=$?

echo ""
echo "=== Analytics tests ==="
python test_2_analytics.py
ANALYTICS_EXIT=$?

echo ""
echo "=== cURL Checklist ==="

CREATE=$(curl -s -i -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"value":"https://example.com"}')

echo "$CREATE"

ID=$(echo "$CREATE" | python -c 'import sys,re; s=sys.stdin.read(); m=re.search(r"\"id\"\s*:\s*\"([^\"]+)\"", s); print(m.group(1) if m else "")')

echo "ID is: $ID"

echo "GET /$ID (expect 301 + value + clicks=1)"
curl -s -i "http://127.0.0.1:8000/$ID"
echo ""

echo "GET /$ID again (expect clicks=2)"
curl -s -i "http://127.0.0.1:8000/$ID"
echo ""

echo "GET / (expect list contains id)"
curl -s -i http://127.0.0.1:8000/
echo ""

echo "PUT /$ID (expect 200)"
curl -s -i -X PUT "http://127.0.0.1:8000/$ID" \
  -H "Content-Type: application/json" \
  -d '{"value":"https://wikipedia.org"}'
echo ""

echo "GET /$ID (expect wikipedia, clicks=3 preserved after PUT)"
curl -s -i "http://127.0.0.1:8000/$ID"
echo ""

echo "DELETE /$ID (expect 204)"
curl -s -i -X DELETE "http://127.0.0.1:8000/$ID"
echo ""

echo "GET /$ID (expect 404, no analytics)"
curl -s -i "http://127.0.0.1:8000/$ID"
echo ""

echo "POST invalid (expect 400 + error)"
curl -s -i -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"value":"not-a-url"}'
echo ""

if [ "$MARK_EXIT" -ne 0 ] || [ "$ANALYTICS_EXIT" -ne 0 ]; then
  echo "FAIL: marking=$MARK_EXIT analytics=$ANALYTICS_EXIT"
  exit 1
fi

echo "ALL TESTS PASSED"
exit 0
