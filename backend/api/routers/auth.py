from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.api.config import get_settings
from backend.api.deps import get_current_user
from backend.api.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    TokenResponse,
    UserOut,
)
from backend.api.security import create_access_token
from database import auth as db_auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request):
    ok, result = db_auth.verify_login_credentials(body.username_or_email, body.password)
    ip = request.client.host if request.client else None
    if not ok:
        db_auth.write_audit_log(
            action="LOGIN_FAILED",
            performed_by_user_id=None,
            target_user_id=None,
            ip_address=ip,
            description=f"Failed login for {body.username_or_email}",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result)
    db_auth.write_audit_log(
        action="LOGIN_SUCCESS",
        performed_by_user_id=result["id"],
        target_user_id=result["id"],
        ip_address=ip,
        description=f"Successful login for {result['username']}",
    )
    settings = get_settings()
    token = create_access_token(
        {
            "sub": str(result["id"]),
            "username": result["username"],
            "email": result["email"],
            "role": result["role"],
            "full_name": result["full_name"],
        },
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenResponse(access_token=token)


@router.post("/forgot-password", response_model=dict)
def forgot_password(_body: ForgotPasswordRequest):
    """
    Accept reset requests without revealing whether the account exists.
    Email delivery can be wired later; lab admins typically reset access manually.
    """
    return {
        "message": "If an account matches this email or username, contact your system administrator for password recovery.",
    }


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    row = db_auth.get_user_by_id(user["id"])
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(**row)


@router.post("/logout")
async def logout():
    return {"message": "Token discarded on client"}
