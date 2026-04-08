from __future__ import annotations

import threading
import uuid
from typing import Any, Callable, Dict, Optional

_jobs_lock = threading.Lock()
_jobs: Dict[str, dict[str, Any]] = {}


def create_job() -> str:
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "",
            "result": None,
            "error": None,
            "log_lines": [],
        }
    return job_id


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    with _jobs_lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def _set_job(job_id: str, **kwargs) -> None:
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def run_zebrazoom_job(
    job_id: str,
    video_path: str,
    config_path: Optional[str],
    output_dir: Optional[str],
    zebrazoom_factory: Callable[[], Any],
) -> None:
    def worker():
        _set_job(job_id, status="running", message="Starting", progress=5)
        try:
            zz = zebrazoom_factory()
            if not zz or not zz.is_available():
                _set_job(
                    job_id,
                    status="failed",
                    error="ZebraZoom is not available on this machine",
                    progress=0,
                )
                return

            def cb(p: int):
                _set_job(job_id, progress=min(95, int(p)), message="Analyzing")

            result = zz.analyze_video(
                video_path,
                config_path,
                output_dir=output_dir,
                progress_callback=cb,
            )
            _set_job(job_id, status="completed", progress=100, message="Done", result=result)
        except Exception as e:
            _set_job(job_id, status="failed", error=str(e), message="Error")

    threading.Thread(target=worker, name=f"analysis-{job_id[:8]}", daemon=True).start()
