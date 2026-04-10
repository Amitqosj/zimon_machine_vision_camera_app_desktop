from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from backend.api.security import decode_token
from database import auth as db_auth

bearer_scheme = HTTPBearer(auto_error=False)


def _payload_to_user(payload: dict) -> dict:
    uid = payload.get("sub")
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    try:
        user_id = int(uid)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token")
    return {
        "id": user_id,
        "username": payload.get("username", ""),
        "email": payload.get("email", ""),
        "role": payload.get("role", "user"),
        "full_name": payload.get("full_name", ""),
    }


async def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(creds.credentials)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _payload_to_user(payload)


async def get_current_user_bearer_or_query(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    access_token: Optional[str] = Query(None),
) -> dict:
    raw = (creds.credentials if creds and creds.credentials else None) or access_token
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(raw)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _payload_to_user(payload)


async def require_admin(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    # Validate admin privilege against current DB state, not only JWT claims.
    # This avoids stale-token mismatches where /auth/me shows admin but
    # admin-protected routes still reject based on old token role.
    row = db_auth.get_user_by_id(int(user["id"]))
    if not row or (row.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
