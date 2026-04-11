from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_current_user
from backend.api.schemas import NotificationOut
from database import notifications as db_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: Annotated[dict, Depends(get_current_user)]):
    return db_notifications.list_for_user(int(user["id"]))


@router.post("/mark-as-read/{notification_id}", response_model=dict)
def mark_as_read(notification_id: int, user: Annotated[dict, Depends(get_current_user)]):
    ok = db_notifications.mark_read(notification_id, int(user["id"]))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"ok": True}


@router.post("/calibration-completed", response_model=dict)
def calibration_completed(user: Annotated[dict, Depends(get_current_user)]):
    db_notifications.create_notification(
        title="Calibration completed",
        message=f"User {user.get('username', 'user')} marked calibration as completed.",
        user_id=int(user["id"]),
    )
    return {"ok": True}
