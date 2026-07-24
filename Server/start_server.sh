#!/usr/bin/env bash
# YunSeok FastAPI 서버 실행 스크립트
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

HOST=0.0.0.0
PORT=8000

# 1) 이미 떠 있는 서버 종료
if pgrep -f "uvicorn main:app" >/dev/null; then
  echo "[*] 기존 서버를 종료합니다..."
  pkill -f "uvicorn main:app"
  sleep 2
fi

# 2) 연동 서비스 확인 (응답이 없어도 서버는 그대로 시작합니다)
port_open() { timeout 1 bash -c "</dev/tcp/127.0.0.1/$1" 2>/dev/null; }

port_open 3306 && echo "[O] MySQL (3306)       연결 확인" || echo "[X] MySQL (3306)       응답 없음 -> 회원가입/로그인 실패합니다"
port_open 8080 && echo "[O] llama-server (8080) 연결 확인" || echo "[X] llama-server (8080) 응답 없음 -> NPC 대화 실패합니다"

# 3) 서버 시작
echo
echo "[*] 서버 주소: http://$(hostname -I | awk '{print $1}'):$PORT"
echo "[*] API 문서 : http://$(hostname -I | awk '{print $1}'):$PORT/docs"
echo "[*] 종료하려면 Ctrl+C"
echo
exec venv/bin/python -m uvicorn main:app --host "$HOST" --port "$PORT"
