import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from backend.api import qt_bridge
from backend.api.deps import get_current_user, get_current_user_bearer_or_query
from backend.api.schemas import CameraSettingRequest

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/list")
def camera_list(_user: dict = Depends(get_current_user)):
    try:
        names = qt_bridge.list_cameras()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"cameras": names}


@router.post("/refresh")
def camera_refresh(_user: dict = Depends(get_current_user)):
    try:
        names = qt_bridge.refresh_cameras()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"cameras": names}


@router.get("/preview/status")
def camera_preview_status(_user: dict = Depends(get_current_user)):
    try:
        previewing = qt_bridge.list_previewing_cameras()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"previewing": previewing}


@router.post("/preview/start")
def preview_start(camera_name: str, _user: dict = Depends(get_current_user)):
    try:
        ok = qt_bridge.start_preview(camera_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not ok:
        raise HTTPException(status_code=400, detail="Could not start preview")
    return {"ok": True, "camera": camera_name}


@router.post("/preview/stop")
def preview_stop(camera_name: str, _user: dict = Depends(get_current_user)):
    try:
        qt_bridge.stop_preview(camera_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}


@router.post("/settings")
def camera_settings(body: CameraSettingRequest, camera_name: str, _user: dict = Depends(get_current_user)):
    try:
        ok = qt_bridge.set_camera_setting(camera_name, body.setting, body.value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not ok:
        raise HTTPException(status_code=400, detail="Setting not applied")
    return {"ok": True}


@router.get("/supported-resolutions")
def camera_supported_resolutions(camera_name: str, _user: dict = Depends(get_current_user)):
    try:
        pairs = qt_bridge.supported_resolutions(camera_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"resolutions": [{"width": w, "height": h} for w, h in pairs]}


@router.get("/meta")
def camera_meta(camera_name: str, _user: dict = Depends(get_current_user)):
    try:
        meta = qt_bridge.get_camera_meta(camera_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown camera")
    return meta


async def _mjpeg_generator():
    boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
    while True:
        jpeg = qt_bridge.get_stream_jpeg()
        if jpeg:
            yield boundary + jpeg + b"\r\n"
        await asyncio.sleep(1 / 20.0)


@router.get("/stream")
async def camera_stream(_user: dict = Depends(get_current_user_bearer_or_query)):
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/snapshot")
def camera_snapshot(_user: dict = Depends(get_current_user_bearer_or_query)):
    jpeg = qt_bridge.get_stream_jpeg()
    if not jpeg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No frame yet; start preview first")
    return Response(content=jpeg, media_type="image/jpeg")
