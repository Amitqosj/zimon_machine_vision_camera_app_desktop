from fastapi import APIRouter, Depends, HTTPException

from backend.api.app_state import get_runner
from backend.api.deps import get_current_user
from backend.api.schemas import ExperimentStartRequest

router = APIRouter(prefix="/experiment", tags=["experiment"])


@router.post("/start")
def experiment_start(body: ExperimentStartRequest, _user: dict = Depends(get_current_user)):
    cfg = {
        "duration_s": body.duration_s,
        "filename_prefix": body.filename_prefix,
        "camera_list": body.camera_list,
        "stimuli": body.stimuli,
    }
    ok = get_runner().start(cfg)
    if not ok:
        raise HTTPException(status_code=409, detail="Experiment already running")
    return {"ok": True}


@router.post("/stop")
def experiment_stop(_user: dict = Depends(get_current_user)):
    get_runner().stop()
    return {"ok": True}


@router.get("/status")
def experiment_status(_user: dict = Depends(get_current_user)):
    return {"running": get_runner().is_running()}
