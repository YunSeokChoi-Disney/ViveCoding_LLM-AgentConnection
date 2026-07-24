#!/usr/bin/env bash
# 두뇌(Brain) LLM 서버 - gemma4 (llama.cpp)
# OpenCode / Hermes Agent 가 이 서버를 모델 제공자로 사용합니다.
# NPC 채팅용 Hermes 서버(start_llm.sh, 8080)와는 별개 프로세스/포트입니다.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

BIN_DIR="bin/llama-b10099"
MODEL="models/gemma-4-E2B-it-Q8_0.gguf"
HOST=127.0.0.1
PORT=8081

# GPU 오프로드 레이어. RTX 3060 드라이버 정상화(재부팅) 후 99로 변경.
NGL=0

if [ ! -f "$MODEL" ]; then
  echo "[X] 모델 파일이 없습니다: $MODEL (다운로드 확인: models/gemma-wget.log)"
  exit 1
fi

if pgrep -f "llama-server .*$PORT" >/dev/null; then
  echo "[*] 기존 두뇌 서버를 종료합니다..."
  pkill -f "llama-server .*$PORT"
  sleep 2
fi

export LD_LIBRARY_PATH="$(pwd)/$BIN_DIR:${LD_LIBRARY_PATH:-}"

echo "[*] 두뇌(gemma4) LLM 서버 시작: http://$HOST:$PORT"
echo "[*] OpenAI 호환 엔드포인트: http://$HOST:$PORT/v1"
echo "[*] GPU 오프로드(-ngl): $NGL  (0=CPU)"
echo "[*] 종료하려면 Ctrl+C"
echo
exec "$BIN_DIR/llama-server" \
  -m "$MODEL" \
  --alias gemma4 \
  --host "$HOST" \
  --port "$PORT" \
  -c 65536 \
  -t 6 \
  -ngl "$NGL"
