#!/usr/bin/env bash
set -e

source .venv/bin/activate

python run.py & SERVER_PID=$!
sleep 0.6

echo "Running marking tests..."
python test_1_marking_mk2.py
TEST_EXIT=$?

echo "cURL Checklist..."

CREATE=$(curl -s -i -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"value":"https://example.com"}')

echo "$CREATE"

ID=$(echo "$CREATE" | python -c 'import sys,re; s=sys.stdin.read(); m=re.search(r"\"id\"\s*:\s*\"([^\"]+)\"", s); print(m.group(1) if m else "")')

echo "ID is: $ID"

echo "GET /$ID (expect 301 + value)"
curl -i "http://127.0.0.1:8000/$ID"

echo "GET / (expect list contains id)"
curl -i http://127.0.0.1:8000/

echo "PUT /$ID (expect 200)"
curl -i -X PUT "http://127.0.0.1:8000/$ID" \
  -H "Content-Type: application/json" \
  -d '{"value":"https://wikipedia.org"}'

echo "GET /$ID (expect wikipedia)"
curl -i "http://127.0.0.1:8000/$ID"

echo "DELETE /$ID (expect 204)"
curl -i -X DELETE "http://127.0.0.1:8000/$ID"

echo "GET /$ID (expect 404)"
curl -i "http://127.0.0.1:8000/$ID"

echo "POST invalid (expect 400 + error)"
curl -i -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"value":"not-a-url"}'

echo "Stopping server..."
kill "$SERVER_PID"
wait "$SERVER_PID" 2>/dev/null || true

exit "$TEST_EXIT"
