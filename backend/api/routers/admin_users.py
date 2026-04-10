import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.api.config import get_settings
from backend.api.deps import require_admin
from backend.api.schemas import (
    AdminCreateStudentRequest,
    AdminUpdateStudentRequest,
    PasswordResetRequest,
    RecoveryResetRequest,
    UserOut,
)
from database import auth as db_auth
from database import notifications as db_notifications

logger = logging.getLogger("zimon.api.auth")

router = APIRouter(prefix="/users", tags=["users"])
recovery_router = APIRouter(prefix="/internal", tags=["internal-recovery"])


@router.get("", response_model=list[UserOut])
def list_users(_admin: Annotated[dict, Depends(require_admin)]):
    return db_auth.list_users()


@router.post("", response_model=UserOut)
def create_student(
    body: AdminCreateStudentRequest,
    request: Request,
    admin: Annotated[dict, Depends(require_admin)],
):
    ok, result = db_auth.create_user(
        full_name=body.full_name,
        username=body.username,
        email=body.email,
        password=body.password,
        role=db_auth.ROLE_STUDENT,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(result or "Unable to create student"))
    created = db_auth.get_user_by_id(int(result))
    db_auth.write_audit_log(
        action="ADMIN_CREATE_STUDENT",
        performed_by_user_id=admin["id"],
        target_user_id=created["id"],
        ip_address=request.client.host if request.client else None,
        description=f"Admin created student {created['username']}",
    )
    db_notifications.create_notification(
        title="Student added",
        message=f"Admin {admin.get('username', 'admin')} added student {created['username']}.",
        user_id=None,
    )
    return created


@router.put("/{user_id}", response_model=UserOut)
def update_student(
    user_id: int,
    body: AdminUpdateStudentRequest,
    request: Request,
    admin: Annotated[dict, Depends(require_admin)],
):
    target = db_auth.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target["role"] != db_auth.ROLE_STUDENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only student accounts can be edited")
    ok = db_auth.update_user(user_id=user_id, full_name=body.full_name, email=body.email, is_active=body.is_active)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to update student")
    updated = db_auth.get_user_by_id(user_id)
    db_auth.write_audit_log(
        action="ADMIN_UPDATE_STUDENT",
        performed_by_user_id=admin["id"],
        target_user_id=user_id,
        ip_address=request.client.host if request.client else None,
        description=f"Admin updated student {updated['username']}",
    )
    return updated


@router.post("/{user_id}/reset-password", response_model=dict)
def reset_student_password(
    user_id: int,
    body: PasswordResetRequest,
    request: Request,
    admin: Annotated[dict, Depends(require_admin)],
):
    target = db_auth.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target["role"] != db_auth.ROLE_STUDENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only student accounts can be reset")
    ok = db_auth.set_user_password(user_id=user_id, new_password=body.new_password, unlock=True)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to reset password")
    db_auth.write_audit_log(
        action="ADMIN_RESET_STUDENT_PASSWORD",
        performed_by_user_id=admin["id"],
        target_user_id=user_id,
        ip_address=request.client.host if request.client else None,
        description=f"Admin reset password for student {target['username']}",
    )
    return {"message": "Student password reset successfully"}


@router.post("/{user_id}/lock", response_model=dict)
def lock_student(user_id: int, request: Request, admin: Annotated[dict, Depends(require_admin)]):
    target = db_auth.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target["role"] != db_auth.ROLE_STUDENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only student accounts can be locked")
    db_auth.set_user_lock_state(user_id, True)
    db_auth.write_audit_log(
        action="ADMIN_LOCK_STUDENT",
        performed_by_user_id=admin["id"],
        target_user_id=user_id,
        ip_address=request.client.host if request.client else None,
        description=f"Admin locked student {target['username']}",
    )
    return {"message": "Student locked"}


@router.post("/{user_id}/unlock", response_model=dict)
def unlock_student(user_id: int, request: Request, admin: Annotated[dict, Depends(require_admin)]):
    target = db_auth.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target["role"] != db_auth.ROLE_STUDENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only student accounts can be unlocked")
    db_auth.set_user_lock_state(user_id, False)
    db_auth.write_audit_log(
        action="ADMIN_UNLOCK_STUDENT",
        performed_by_user_id=admin["id"],
        target_user_id=user_id,
        ip_address=request.client.host if request.client else None,
        description=f"Admin unlocked student {target['username']}",
    )
    return {"message": "Student unlocked"}


@recovery_router.post("/recovery-access", response_model=dict)
def recovery_reset_admin(body: RecoveryResetRequest, request: Request):
    settings = get_settings()
    if not settings.recovery_secret_key:
        logger.error("Recovery endpoint configured without secret")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recovery unavailable")

    if not hmac.compare_digest(body.secret_key, settings.recovery_secret_key):
        db_auth.write_audit_log(
            action="RECOVERY_FAILED",
            performed_by_user_id=None,
            target_user_id=None,
            ip_address=request.client.host if request.client else None,
            description=f"Invalid recovery secret for {body.admin_username_or_email}",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recovery denied")

    request_ip = request.client.host if request.client else ""
    allow_ips = settings.recovery_ip_list
    if allow_ips and request_ip not in allow_ips:
        db_auth.write_audit_log(
            action="RECOVERY_FAILED",
            performed_by_user_id=None,
            target_user_id=None,
            ip_address=request_ip,
            description=f"Recovery blocked by IP policy for {body.admin_username_or_email}",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recovery denied")

    target = db_auth.get_user_by_username_or_email(body.admin_username_or_email)
    if not target or target["role"] != db_auth.ROLE_ADMIN:
        db_auth.write_audit_log(
            action="RECOVERY_FAILED",
            performed_by_user_id=None,
            target_user_id=None,
            ip_address=request_ip,
            description=f"Recovery target not found or not admin: {body.admin_username_or_email}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recovery target")

    db_auth.set_user_password(target["id"], body.new_password, unlock=True)
    db_auth.set_user_active_state(target["id"], True)
    db_auth.write_audit_log(
        action="RECOVERY_ADMIN_PASSWORD_RESET",
        performed_by_user_id=None,
        target_user_id=target["id"],
        ip_address=request_ip,
        description=f"Recovery reset admin {target['username']}",
    )
    return {"message": "Admin password reset and account unlocked"}
