#!/usr/bin/env bash
# 在一般電腦上啟動工作室系統：建立 venv、安裝套件、開服務並打開瀏覽器。
#
#   ./start-local.sh              啟動服務（預設 port 8000）
#   ./start-local.sh --simulate   改開鍵盤模擬讀卡機（需服務已在另一個視窗跑）
#   ./start-local.sh --no-browser 啟動但不自動開瀏覽器
#   PORT=9000 ./start-local.sh    換 port
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
OPEN_BROWSER=1
SIMULATE=0
for arg in "$@"; do
    case "$arg" in
        --simulate) SIMULATE=1 ;;
        --no-browser) OPEN_BROWSER=0 ;;
        -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "未知參數：$arg（可用 --simulate、--no-browser、--help）" >&2; exit 2 ;;
    esac
done

# --- Python 3.11 以上 -------------------------------------------------------
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "找不到 $PY。請先安裝 Python 3.11 以上，或用 PYTHON=/path/to/python3 指定。" >&2
    exit 1
fi
if ! "$PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "需要 Python 3.11 以上，目前是 $("$PY" -V 2>&1)。" >&2
    echo "macOS 可用 brew install python@3.11，然後 PYTHON=python3.11 ./start-local.sh" >&2
    exit 1
fi

# --- venv 與套件（requirements 沒變就跳過安裝） -----------------------------
if [ ! -d .venv ]; then
    echo "建立 .venv ..."
    "$PY" -m venv .venv
fi
VENV_PY=.venv/bin/python
[ -x "$VENV_PY" ] || VENV_PY=.venv/Scripts/python.exe   # Git Bash on Windows

STAMP=.venv/.requirements-stamp
# requests 不在 requirements.txt 裡，但 --simulate 需要它。
if ! cmp -s requirements.txt "$STAMP"; then
    echo "安裝套件 ..."
    "$VENV_PY" -m pip install --quiet --upgrade pip
    "$VENV_PY" -m pip install --quiet -r requirements.txt requests
    cp requirements.txt "$STAMP"
fi

if [ "$SIMULATE" = "1" ]; then
    echo "模擬讀卡機（Ctrl+C 結束）。先在後台建立使用者並填好卡片 UID，再在這裡輸入同一組。"
    exec "$VENV_PY" services/nfc_reader.py --simulate --api-url "http://127.0.0.1:${PORT}"
fi

# --- 設定 -------------------------------------------------------------------
if [ -f .env ]; then
    set -a; . ./.env; set +a
fi

DB_PATH="data/studio.db"
if [ ! -f "$DB_PATH" ] && [ -z "${ADMIN_PASSWORD:-}" ] && [ -t 0 ]; then
    echo "首次啟動，資料庫還不存在。"
    printf "請設定管理員密碼（直接按 Enter 讓系統隨機產生）: "
    read -r -s ADMIN_PASSWORD
    printf "\n"
    export ADMIN_PASSWORD
fi

URL="http://127.0.0.1:${PORT}"
echo
echo "  打卡站  ${URL}/"
echo "  管理後台 ${URL}/admin   帳號 admin"
echo "  API 文件 ${URL}/docs"
echo "  沒有讀卡機？另開一個視窗跑：./start-local.sh --simulate"
echo "  停止：Ctrl+C"
echo

# 服務起來後再開瀏覽器；uvicorn 留在前景，Ctrl+C 才收得乾淨。
if [ "$OPEN_BROWSER" = "1" ]; then
    (
        for _ in $(seq 1 60); do
            if "$VENV_PY" -c "
import socket, sys
s = socket.socket()
s.settimeout(0.5)
sys.exit(0 if s.connect_ex(('127.0.0.1', ${PORT})) == 0 else 1)
" 2>/dev/null; then
                if command -v open >/dev/null 2>&1; then open "$URL"
                elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
                fi
                exit 0
            fi
            sleep 0.5
        done
    ) &
fi

exec "$VENV_PY" -m uvicorn app.main:app --reload --host 127.0.0.1 --port "$PORT"
