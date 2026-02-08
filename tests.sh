#!/usr/bin/env bash
source .venv/bin/activate
lsof -ti:8000 | xargs kill -9 2>/dev/null
python run.py & PID=$!; sleep 0.6
trap "kill $PID 2>/dev/null; wait $PID 2>/dev/null" EXIT

run_bonus() {
  echo "  1) Custom ID"
  echo "  2) Analytics"
  echo "  3) Expiration"
  echo "  4) Filter/Sort"
  echo "  5) Bulk"
  echo "  6) All"
  read -p "  > " b
  case $b in
    1) python -m pytest test_2_bonus.py -k "custom_id" -v ;;
    2) python -m pytest test_2_bonus.py -k "analytics or put_keeps" -v ;;
    3) python -m pytest test_2_bonus.py -k "expir" -v ;;
    4) python -m pytest test_2_bonus.py -k "filter or sort" -v ;;
    5) python -m pytest test_2_bonus.py -k "bulk" -v ;;
    6) python test_2_bonus.py ;;
    *) echo "invalid" ;;
  esac
}

while true; do
  echo "Tests"
  echo "1) Marking"
  echo "2) Bonus"
  echo "q) Quit"
  read -p "> " c
  case $c in
    1) python test_1_marking_mk2.py ;;
    2) run_bonus ;;
    q|Q) break ;; *) echo "invalid" ;;
  esac
done
