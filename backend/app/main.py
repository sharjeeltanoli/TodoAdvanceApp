import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.routes import todos, chat, history, notifications

logger = logging.getLogger(__name__)

# When DAPR_ENABLED=false (e.g. Render free tier), skip Dapr-dependent
# routers (SSE proxy, event handlers, cron bindings).
# Notifications router is always registered: /unread-count is DB-only and
# the other endpoints degrade gracefully to 503 when Dapr isn't running.
DAPR_ENABLED = os.getenv("DAPR_ENABLED", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Hackathon Todo API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Always-on routes — no Dapr dependency
app.include_router(todos.router, prefix="/api")
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(notifications.router)  # /unread-count is DB-only; others degrade to 503

# Dapr-dependent routes — only registered when Dapr sidecar is available
if DAPR_ENABLED:
    from app.routes import sse_proxy
    from app.events import handlers as event_handlers

    app.include_router(event_handlers.router)
    app.include_router(sse_proxy.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if DAPR_ENABLED:
    @app.get("/dapr/subscribe")
    async def dapr_subscribe():
        """Dapr programmatic subscription endpoint."""
        return [
            {
                "pubsubname": "pubsub",
                "topic": "task-events",
                "route": "/events/task",
            },
        ]
