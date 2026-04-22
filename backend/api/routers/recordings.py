import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.api.deps import get_current_user, get_current_user_bearer_or_query

router = APIRouter(prefix="/recordings", tags=["recordings"])

VIDEO_EXT = frozenset({".mp4", ".avi", ".mkv", ".mov", ".webm", ".m4v"})


def recordings_root() -> Path:
    env = os.environ.get("ZIMON_RECORDINGS_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    preferred = Path("D:/Zimon")
    if Path("D:/").exists():
        return preferred.resolve()
    return (Path.cwd() / "recordings").resolve()


def _safe_file_under_root(root: Path, rel: str) -> Path | None:
    if not rel or rel.startswith(("/", "\\")):
        return None
    parts = Path(rel).parts
    if ".." in parts:
        return None
    full = (root / rel).resolve()
    root_r = root.resolve()
    try:
        full.relative_to(root_r)
    except ValueError:
        return None
    if not full.is_file():
        return None
    return full


@router.get("/list")
def list_recordings(_user: dict = Depends(get_current_user)):
    root = recordings_root()
    if not root.is_dir():
        return {"root": str(root), "items": []}

    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in VIDEO_EXT:
            files.append(p)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for p in files[:500]:
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        st = p.stat()
        items.append(
            {
                "relpath": rel,
                "full_path": str(p.resolve()),
                "name": p.name,
                "size": st.st_size,
                "modified_iso": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return {"root": str(root), "items": items}


@router.get("/media")
def recording_media(
    path: str = Query(..., min_length=1, description="Path relative to recordings root"),
    _user: dict = Depends(get_current_user_bearer_or_query),
):
    root = recordings_root()
    full = _safe_file_under_root(root, path.replace("\\", "/"))
    if full is None:
        raise HTTPException(status_code=404, detail="File not found")
    media = "application/octet-stream"
    suf = full.suffix.lower()
    if suf == ".mp4":
        media = "video/mp4"
    elif suf == ".webm":
        media = "video/webm"
    return FileResponse(str(full), media_type=media, filename=full.name)
