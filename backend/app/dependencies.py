import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_session),
) -> str:
    """Validate Bearer token by querying the Better Auth session table directly.

    The backend and frontend share the same Neon database, so we can look up
    the session token without an HTTP round-trip to BETTER_AUTH_URL. This
    removes the dependency on BETTER_AUTH_URL being reachable from the backend
    and works identically on local dev, Kubernetes, and Render.

    Better Auth stores sessions in the 'session' table (camelCase columns):
        token     — opaque session token sent in the Authorization header
        userId    — the authenticated user's ID
        expiresAt — expiry timestamp
    """
    result = await db.execute(
        text(
            'SELECT "userId" FROM session'
            ' WHERE token = :token AND "expiresAt" > NOW()'
        ),
        {"token": credentials.credentials},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return row[0]


async def get_current_user_from_request(request: Request, token: str) -> str | None:
    """Validate a raw Bearer token string (for SSE proxy use cases).

    Falls back to HTTP call since SSE gateway doesn't have a DB session injected.
    Returns user_id on success, None on failure (no exception raised).
    """
    try:
        auth_base = settings.BACKEND_BETTER_AUTH_URL or settings.BETTER_AUTH_URL
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{auth_base}/api/auth/get-session",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code == 200:
            data = response.json()
            return data.get("user", {}).get("id")
    except Exception:
        pass
    return None
