import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.routes import todos, chat, notifications, history, sse_proxy
from app.events import handlers as event_handlers

logger = logging.getLogger(__name__)


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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(todos.router, prefix="/api")
app.include_router(chat.router)
app.include_router(event_handlers.router)
app.include_router(notifications.router)
app.include_router(history.router)
app.include_router(sse_proxy.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """Dapr programmatic subscription endpoint.

    Returns the list of topic subscriptions for this service.
    """
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task",
        },
    ]
