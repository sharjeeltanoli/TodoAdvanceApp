import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables, engine
from app.routes import todos, chat

logger = logging.getLogger(__name__)


async def run_scheduler():
    """Background loop that processes recurring tasks every 5 minutes."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.scheduler import process_recurring_tasks

    while True:
        await asyncio.sleep(300)  # 5 minutes
        try:
            async with AsyncSession(engine) as session:
                await process_recurring_tasks(session)
        except Exception:
            logger.exception("Scheduler error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    task = asyncio.create_task(run_scheduler())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


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


@app.get("/health")
async def health():
    return {"status": "ok"}
