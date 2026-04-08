from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.analysis_jobs import create_job, get_job, run_zebrazoom_job
from backend.api.app_state import get_zebrazoom
from backend.api.deps import get_current_user
from backend.api.schemas import AnalysisStartRequest

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/available")
def analysis_available(_user: dict = Depends(get_current_user)):
    z = get_zebrazoom()
    return {"available": bool(z and z.is_available())}


@router.post("/jobs")
def start_analysis(body: AnalysisStartRequest, _user: dict = Depends(get_current_user)):
    job_id = create_job()
    run_zebrazoom_job(
        job_id,
        body.video_path,
        body.config_path,
        body.output_dir,
        zebrazoom_factory=get_zebrazoom,
    )
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def analysis_job_status(job_id: str, _user: dict = Depends(get_current_user)):
    j = get_job(job_id)
    if not j:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job")
    return j
