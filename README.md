# ViveCoding — LLM · Agent Connection

**두뇌(LLM)와 행동(Agent)을 분리해 연결하는** 로컬 AI 구성 + FastAPI 게임 서버 프로젝트.

- **두뇌 (Brain)** = 사고를 담당하는 로컬 LLM (llama.cpp)
- **행동 (Agent)** = 코딩·실행을 담당하는 에이전트 (OpenCode, Hermes Agent)
- 두 에이전트가 하나의 두뇌 LLM에 OpenAI 호환 API로 연결됨
- 별도로, FastAPI 게임 서버가 NPC 채팅용 LLM을 사용

모든 LLM은 **로컬(llama.cpp)** 에서 구동되어 외부 API 비용·의존이 없습니다.

---

## 워크플로우

```mermaid
flowchart TD
    subgraph Agents["행동 (Agents)"]
        OC["OpenCode<br/>~/.config/opencode/opencode.json"]
        HA["Hermes Agent<br/>~/.hermes/config.yaml"]
    end

    subgraph Brain["두뇌 (Brain)"]
        BRAIN["gemma4 (llama.cpp)<br/>127.0.0.1:8081 · 64K ctx<br/>start_brain.sh"]
    end

    subgraph Game["게임 서버 (별개 경로)"]
        API["FastAPI 서버<br/>0.0.0.0:8000<br/>start_server.sh"]
        NPC["Hermes-3-8B (llama.cpp)<br/>127.0.0.1:8080<br/>start_llm.sh"]
        DB[("MySQL<br/>:3306")]
    end

    Client["게임 클라이언트"]

    OC -- "OpenAI 호환 /v1" --> BRAIN
    HA -- "OpenAI 호환 /v1" --> BRAIN

    Client -- "회원가입/로그인/NPC 대화" --> API
    API -- "인증·유저" --> DB
    API -- "NPC 채팅 프록시 /v1/chat/completions" --> NPC
```

> **주의:** "Hermes"가 두 곳에 나옵니다 — (1) NPC용 **Hermes-3-8B 모델**, (2) 코딩 에이전트 도구 **Hermes Agent**. 서로 다른 것입니다.

---

## 구성 요소

| 구성 | 역할 | 포트 | 모델 |
|---|---|---|---|
| **gemma4 두뇌** | OpenCode / Hermes Agent의 사고 엔진 | `8081` | `gemma-4-E2B-it-Q8_0.gguf` |
| **NPC LLM** | FastAPI 게임 서버의 NPC 대화 | `8080` | `Hermes-3-Llama-3.1-8B.Q4_K_M.gguf` |
| **FastAPI 서버** | 인증 + NPC 채팅 API | `8000` | — |
| **MySQL** | 유저 저장소 | `3306` | — |

에이전트 → 두뇌 연결 설정 (저장소 밖, 각 홈 디렉토리):

| 에이전트 | 설정 파일 | 연결 |
|---|---|---|
| OpenCode | `~/.config/opencode/opencode.json` | provider `llamacpp` → `http://127.0.0.1:8081/v1`, model `llamacpp/gemma4` |
| Hermes Agent | `~/.hermes/config.yaml` | provider `custom` → `http://127.0.0.1:8081/v1`, model `gemma4` |

---

## 디렉토리 구조

```
ViveCoding_LLM-AgentConnection/
├── Server/                     # FastAPI 게임 서버
│   ├── main.py                 # 앱 진입점 (/health)
│   ├── routers/
│   │   ├── auth.py             # /auth/signup, /auth/login, /auth/withdraw
│   │   └── npc.py              # /npc/chat, /npc/reset (→ llama.cpp 프록시)
│   ├── models.py               # User 테이블 (SQLAlchemy)
│   ├── config.py               # 환경설정 (.env)
│   ├── security.py, deps.py    # JWT · 의존성
│   ├── start_server.sh         # 서버 실행 스크립트
│   └── .env.example            # 환경변수 템플릿
└── llmserver/                  # 로컬 LLM 서버
    ├── start_brain.sh          # gemma4 두뇌 (8081)
    └── start_llm.sh            # Hermes-3-8B NPC (8080)
```

> **git 제외 항목** (`.gitignore`): 모델 가중치 `*.gguf`(약 9.5GB), llama.cpp 바이너리, `venv/`, `.env`(비밀키), 로그.

---

## 설치 및 실행

### 1. 사전 준비
- Python 3.12, MySQL, llama.cpp 바이너리(`llmserver/bin/`), 모델 GGUF(`llmserver/models/`)
- `Server/.env` 작성 (`Server/.env.example` 참고 — DB 접속정보·`JWT_SECRET_KEY` 등)

### 2. 두뇌 LLM (에이전트용)
```bash
./llmserver/start_brain.sh          # gemma4 → 127.0.0.1:8081 (64K 컨텍스트)
```

### 3. 게임 서버 + NPC LLM
```bash
./llmserver/start_llm.sh            # Hermes-3-8B → 127.0.0.1:8080
cd Server && ./start_server.sh      # FastAPI → 0.0.0.0:8000
```

### 4. 에이전트 실행 (두뇌에 연결됨)
```bash
opencode                            # 또는
hermes
```

---

## 주요 API (FastAPI, `:8000`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 헬스체크 |
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 (JWT 발급) |
| POST | `/auth/withdraw` | 회원 탈퇴 |
| POST | `/npc/chat` | NPC 대화 (LLM 응답) |
| POST | `/npc/reset` | NPC 대화 기록 초기화 |

API 문서: 서버 실행 후 `http://<host>:8000/docs`

---

## 현재 상태 / 남은 과제

- ✅ **OpenCode → gemma4 두뇌**: 연결·동작 검증 완료
- ⚠️ **Hermes Agent → gemma4 두뇌**: 연결은 되나 **CPU 추론이 느려** 실사용이 어려움
- ⚠️ **GPU 미사용**: RTX 3060(12GB) 보유 중이나 드라이버 버전 불일치 상태
  - **재부팅** → 드라이버 정상화 → llama.cpp **CUDA 빌드** → `start_*.sh`의 `NGL=0` → `99`
  - GPU 가속 시 에이전트 속도 문제 해결 예상
