import asyncio
import logging
import os

from fastapi import APIRouter, Depends, HTTPException

from backend.api import settings_store
from backend.api.app_state import get_zebrazoom, invalidate_zebrazoom
from backend.api.deps import get_current_user
from backend.api.schemas import (
    AppSettingsOut,
    AppSettingsUpdate,
    ZebraZoomBrowseOut,
    ZebraZoomTestRequest,
)

logger = logging.getLogger("zimon.api.settings")

router = APIRouter(prefix="/settings", tags=["settings"])


def _native_pick_zebrazoom_exe() -> str:
    """Open a Tk file dialog on the server machine (same as local PyQt-style browse)."""
    root = None
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass
        path = filedialog.askopenfilename(
            parent=root,
            title="Select ZebraZoom.exe",
            filetypes=[
                ("Executable", "*.exe"),
                ("All files", "*.*"),
            ],
        )
        return path.strip() if path else ""
    except Exception as e:
        logger.warning("Native ZebraZoom browse failed: %s", e)
        return ""
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


@router.post("/zebrazoom/browse", response_model=ZebraZoomBrowseOut)
async def zebrazoom_browse_native(_user: dict = Depends(get_current_user)):
    loop = asyncio.get_running_loop()
    path = await loop.run_in_executor(None, _native_pick_zebrazoom_exe)
    return ZebraZoomBrowseOut(path=path, native_dialog=True)


@router.get("", response_model=AppSettingsOut)
def get_app_settings(_user: dict = Depends(get_current_user)):
    data = settings_store.load_settings()
    return AppSettingsOut(zebrazoom_exe=str(data.get("zebrazoom_exe") or ""))


@router.put("", response_model=AppSettingsOut)
def put_app_settings(body: AppSettingsUpdate, _user: dict = Depends(get_current_user)):
    updates = {}
    if body.zebrazoom_exe is not None:
        updates["zebrazoom_exe"] = body.zebrazoom_exe.strip()
    saved = settings_store.save_settings(updates)
    invalidate_zebrazoom()
    return AppSettingsOut(zebrazoom_exe=str(saved.get("zebrazoom_exe") or ""))


@router.post("/zebrazoom/test")
def test_zebrazoom_path(body: ZebraZoomTestRequest, _user: dict = Depends(get_current_user)):
    path = body.path.strip()
    if not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="File does not exist")
    try:
        from backend.zebrazoom_integration import ZebraZoomIntegration

        zz = ZebraZoomIntegration(zebrazoom_path=path)
        ok = zz.is_available()
        return {"ok": ok, "message": "ZebraZoom detected" if ok else "Path saved but not detected as valid ZebraZoom"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/zebrazoom/status")
def zebrazoom_status(_user: dict = Depends(get_current_user)):
    zz = get_zebrazoom()
    path = str(settings_store.load_settings().get("zebrazoom_exe") or "")
    return {
        "configured_path": path,
        "available": bool(zz and zz.is_available()),
        "resolved_exe": getattr(zz, "zebrazoom_exe", None) if zz else None,
    }
