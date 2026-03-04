import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

bearer_scheme = HTTPBearer()


def _auth_base_url() -> str:
    """Return the Better Auth base URL for server-to-server token validation.

    Prefers BACKEND_BETTER_AUTH_URL (in-cluster HTTP) over BETTER_AUTH_URL to
    avoid TLS issues when the external ingress uses a staging/self-signed cert.
    """
    return settings.BACKEND_BETTER_AUTH_URL or settings.BETTER_AUTH_URL


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Validate Bearer token via Better Auth session endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{_auth_base_url()}/api/auth/get-session",
            headers={
                "Authorization": f"Bearer {credentials.credentials}",
            },
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    data = response.json()
    user_id = (data or {}).get("user") or {}
    user_id = user_id.get("id") if isinstance(user_id, dict) else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session data",
        )
    return user_id


async def get_current_user_from_request(request: Request, token: str) -> str | None:
    """Validate a raw Bearer token string (for SSE proxy use cases).

    Returns user_id on success, None on failure (no exception raised).
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{_auth_base_url()}/api/auth/get-session",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code == 200:
            data = response.json()
            return data.get("user", {}).get("id")
    except Exception:
        pass
    return None
