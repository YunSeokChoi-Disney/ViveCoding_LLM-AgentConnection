#!/usr/bin/env bash
# Hermes NPC LLM 서버 (llama.cpp)
# FastAPI(config.py의 LLAMA_SERVER_URL=http://127.0.0.1:8080)가 이 서버를 호출합니다.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

BIN_DIR="bin/llama-b10099"
MODEL="models/Hermes-3-Llama-3.1-8B.Q4_K_M.gguf"
HOST=127.0.0.1
PORT=8080

# GPU 오프로드 레이어 수. RTX 3060 드라이버 정상화(재부팅) 후 99로 바꾸면 GPU 가속.
# 현재 CPU 추론이므로 0.
NGL=0

if [ ! -f "$MODEL" ]; then
  echo "[X] 모델 파일이 없습니다: $MODEL"
  echo "    다운로드가 끝났는지 확인하세요 (models/wget.log)."
  exit 1
fi

# 기존 llama-server 종료
if pgrep -f "llama-server .*$PORT" >/dev/null; then
  echo "[*] 기존 LLM 서버를 종료합니다..."
  pkill -f "llama-server .*$PORT"
  sleep 2
fi

export LD_LIBRARY_PATH="$(pwd)/$BIN_DIR:${LD_LIBRARY_PATH:-}"

echo "[*] Hermes LLM 서버 시작: http://$HOST:$PORT"
echo "[*] GPU 오프로드(-ngl): $NGL  (0=CPU)"
echo "[*] 종료하려면 Ctrl+C"
echo
exec "$BIN_DIR/llama-server" \
  -m "$MODEL" \
  --host "$HOST" \
  --port "$PORT" \
  -c 8192 \
  -t 6 \
  -ngl "$NGL"
