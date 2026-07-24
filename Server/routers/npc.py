import requests
from fastapi import APIRouter, HTTPException, status

from config import settings
from schemas import NpcChatRequest, NpcChatResponse, NpcResetResponse

router = APIRouter(prefix="/npc", tags=["npc"])

# Placeholder persona — edit this to change the NPC's character.
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Elder Maren, a friendly village elder NPC in a fantasy game. "
        "Keep replies to 1-3 short sentences, stay in character, and never mention being an AI."
    ),
}

# Single in-memory conversation, no per-player/session separation.
# Fine for local single-player testing; requires uvicorn to stay single-process.
_history: list[dict] = [SYSTEM_PROMPT]


def _trim_history() -> None:
    max_messages = 1 + settings.NPC_MAX_HISTORY_TURNS * 2
    if len(_history) > max_messages:
        _history[:] = [_history[0]] + _history[-(max_messages - 1):]


@router.post("/chat", response_model=NpcChatResponse)
def chat(request: NpcChatRequest):
    _history.append({"role": "user", "content": request.message})
    _trim_history()

    payload = {
        "model": "gemma",
        "messages": _history,
        "temperature": 0.8,
        "max_tokens": 512,
    }

    try:
        response = requests.post(
            f"{settings.LLAMA_SERVER_URL}/v1/chat/completions",
            json=payload,
            timeout=settings.LLAMA_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        _history.pop()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NPC LLM server is unreachable: {exc}",
        ) from exc

    try:
        reply_text = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        _history.pop()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response shape from LLM server",
        ) from exc

    _history.append({"role": "assistant", "content": reply_text})
    return NpcChatResponse(reply=reply_text)


@router.post("/reset", response_model=NpcResetResponse)
def reset():
    _history[:] = [SYSTEM_PROMPT]
    return NpcResetResponse(message="Conversation history cleared")
