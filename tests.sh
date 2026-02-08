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
echo "=== Bonus tests ==="
python test_2_bonus.py
BONUS_EXIT=$?

if [ "$MARK_EXIT" -ne 0 ] || [ "$BONUS_EXIT" -ne 0 ]; then
  echo "FAIL: marking=$MARK_EXIT bonus=$BONUS_EXIT"
  exit 1
fi

echo "ALL TESTS PASSED"
exit 0
