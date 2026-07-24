from fastapi import FastAPI

from database import init_db
from routers import auth, npc, whatsapp

app = FastAPI(title="SampleProjectClaude Auth Server")

app.include_router(auth.router)
app.include_router(npc.router)
app.include_router(whatsapp.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
