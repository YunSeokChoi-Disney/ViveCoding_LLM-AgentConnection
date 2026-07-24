import hashlib
import hmac
import json
import logging

import requests
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response, status

from config import settings

logger = logging.getLogger("whatsapp")

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Placeholder persona — edit to change the assistant's character.
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful, friendly WhatsApp assistant. "
        "Reply concisely in the user's language."
    ),
}

# Per-sender in-memory conversation history, keyed by phone number.
# Single-process only (requires uvicorn to stay single-process).
_histories: dict[str, list[dict]] = {}


def _history_for(sender: str) -> list[dict]:
    history = _histories.get(sender)
    if history is None:
        history = [SYSTEM_PROMPT]
        _histories[sender] = history
    return history


def _trim_history(history: list[dict]) -> None:
    max_messages = 1 + settings.WHATSAPP_MAX_HISTORY_TURNS * 2
    if len(history) > max_messages:
        history[:] = [history[0]] + history[-(max_messages - 1):]


def _valid_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 (HMAC-SHA256 of the raw body)."""
    if not settings.WHATSAPP_APP_SECRET:
        # No secret configured -> cannot verify; reject to stay safe.
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header[len("sha256="):])


@router.get("/webhook")
def verify_webhook(
    mode: str = Query(default="", alias="hub.mode"),
    token: str = Query(default="", alias="hub.verify_token"),
    challenge: str = Query(default="", alias="hub.challenge"),
):
    """Meta webhook verification handshake."""
    if (
        mode == "subscribe"
        and settings.WHATSAPP_VERIFY_TOKEN
        and token == settings.WHATSAPP_VERIFY_TOKEN
    ):
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="verification failed")


def _generate_reply(sender: str, message: str) -> str:
    history = _history_for(sender)
    history.append({"role": "user", "content": message})
    _trim_history(history)

    payload = {
        "model": "gemma",
        "messages": history,
        "temperature": 0.8,
        "max_tokens": 512,
    }
    response = requests.post(
        f"{settings.WHATSAPP_LLM_URL}/v1/chat/completions",
        json=payload,
        timeout=settings.LLAMA_REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    reply_text = response.json()["choices"][0]["message"]["content"]

    history.append({"role": "assistant", "content": reply_text})
    return reply_text


def _send_message(to: str, text: str) -> None:
    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}"
        f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        },
        timeout=settings.LLAMA_REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def _process_message(sender: str, message: str) -> None:
    """Runs in the background so the webhook can 200 immediately."""
    try:
        reply = _generate_reply(sender, message)
        _send_message(sender, reply)
    except requests.exceptions.RequestException as exc:
        logger.error("WhatsApp message handling failed for %s: %s", sender, exc)


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()

    if not _valid_signature(raw_body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid signature")

    data = json.loads(raw_body)

    # WhatsApp Cloud API payload: entry[].changes[].value.messages[]
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                if message.get("type") != "text":
                    continue
                sender = message["from"]
                body = message["text"]["body"]
                background_tasks.add_task(_process_message, sender, body)

    # Always 200 quickly so Meta does not retry.
    return {"status": "received"}
