from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_current_user
from backend.api.schemas import PresetCreate, PresetOut, PresetUpdate
from database import presets as db_presets

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("", response_model=List[PresetOut])
def list_presets(user: dict = Depends(get_current_user)):
    rows = db_presets.list_presets(user["id"])
    return [PresetOut(**{**r, "created_at": str(r["created_at"]) if r.get("created_at") else None}) for r in rows]


@router.post("", response_model=dict)
def create_preset(body: PresetCreate, user: dict = Depends(get_current_user)):
    pid = db_presets.create_preset(
        user["id"],
        body.name,
        body.description,
        body.video_path,
        body.config_path,
        body.output_dir,
    )
    return {"id": pid}


@router.get("/{preset_id}", response_model=PresetOut)
def get_preset(preset_id: int, user: dict = Depends(get_current_user)):
    r = db_presets.get_preset(user["id"], preset_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")
    return PresetOut(**{**r, "created_at": str(r["created_at"]) if r.get("created_at") else None})


@router.put("/{preset_id}")
def update_preset(preset_id: int, body: PresetUpdate, user: dict = Depends(get_current_user)):
    ok = db_presets.update_preset(
        user["id"],
        preset_id,
        body.name,
        body.description,
        body.video_path,
        body.config_path,
        body.output_dir,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")
    return {"ok": True}


@router.delete("/{preset_id}")
def delete_preset(preset_id: int, user: dict = Depends(get_current_user)):
    ok = db_presets.delete_preset(user["id"], preset_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")
    return {"ok": True}
