"""
Structured Logging Example for hackathon-todo Backend (FastAPI)

This is a complete, runnable example showing how to set up structured
JSON logging with structlog for the FastAPI backend.

Install:
    pip install structlog python-json-logger fastapi uvicorn prometheus-fastapi-instrumentator

Run:
    uvicorn python_structured_logging_example:app --reload
"""

import logging
import sys
import time
import uuid
from contextvars import ContextVar

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ---------------------------------------------------------------------------
# 1. Context Variables (request-scoped)
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="anonymous")

# ---------------------------------------------------------------------------
# 2. Logging Configuration
# ---------------------------------------------------------------------------

ENVIRONMENT = "production"  # Change to "development" for pretty output


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON output (production) or pretty print (dev)."""

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if ENVIRONMENT == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper()))

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# 3. Custom Prometheus Metrics
# ---------------------------------------------------------------------------

tasks_created_total = Counter(
    "tasks_created_total", "Total tasks created", ["user_id"]
)
task_op_duration = Histogram(
    "task_operation_seconds",
    "Task operation duration",
    ["operation"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
task_op_errors = Counter(
    "task_operation_errors_total", "Task operation errors", ["operation"]
)
auth_failures = Counter(
    "auth_failures_total", "Authentication failures", ["method"]
)

# ---------------------------------------------------------------------------
# 4. Logging Middleware
# ---------------------------------------------------------------------------


class LoggingMiddleware(BaseHTTPMiddleware):
    """Attach request context and log every request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(req_id)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
            method=request.method,
            path=request.url.path,
        )

        log = structlog.get_logger("http")
        start = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            log.info(
                "request.completed",
                status=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            response.headers["X-Request-ID"] = req_id
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            log.error(
                "request.failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(duration_ms, 2),
            )
            raise


# ---------------------------------------------------------------------------
# 5. Application
# ---------------------------------------------------------------------------

setup_logging()

app = FastAPI(title="hackathon-todo-backend")
app.add_middleware(LoggingMiddleware)

# Auto-instrument HTTP metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

logger = structlog.get_logger("tasks")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "backend"}


@app.get("/api/tasks")
async def list_tasks():
    """List all tasks — demonstrates info logging."""
    logger.info("tasks.listing")

    # Simulated task list
    tasks = [
        {"id": "1", "title": "Buy groceries", "completed": False},
        {"id": "2", "title": "Write tests", "completed": True},
    ]

    logger.info("tasks.listed", count=len(tasks))
    return {"tasks": tasks}


@app.post("/api/tasks")
async def create_task(request: Request):
    """Create a task — demonstrates metrics + logging."""
    body = await request.json()

    logger.info("task.creating", title=body.get("title"))

    with task_op_duration.labels(operation="create").time():
        try:
            # Simulated creation
            task_id = str(uuid.uuid4())
            tasks_created_total.labels(user_id="demo-user").inc()

            logger.info("task.created", task_id=task_id, title=body.get("title"))
            return {"id": task_id, "title": body.get("title"), "completed": False}

        except Exception as e:
            task_op_errors.labels(operation="create").inc()
            logger.error("task.create_failed", error=str(e))
            raise HTTPException(status_code=500, detail="Task creation failed")


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task — demonstrates warn logging."""
    logger.info("task.deleting", task_id=task_id)

    with task_op_duration.labels(operation="delete").time():
        # Simulated: task not found
        logger.warning("task.not_found", task_id=task_id)
        raise HTTPException(status_code=404, detail="Task not found")


# ---------------------------------------------------------------------------
# Example log output (JSON in production):
#
# {"request_id":"a1b2c3","method":"POST","path":"/api/tasks",
#  "event":"task.created","task_id":"uuid","title":"Buy groceries",
#  "level":"info","logger":"tasks","timestamp":"2026-02-17T10:30:00Z"}
#
# {"request_id":"a1b2c3","method":"POST","path":"/api/tasks",
#  "event":"request.completed","status":200,"duration_ms":12.34,
#  "level":"info","logger":"http","timestamp":"2026-02-17T10:30:00Z"}
# ---------------------------------------------------------------------------
