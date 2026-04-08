from typing import Any, Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    role: str
    is_active: bool = True
    is_locked: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AdminCreateStudentRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=2)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class AdminUpdateStudentRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    is_active: bool = True


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6)


class RecoveryResetRequest(BaseModel):
    secret_key: str = Field(..., min_length=1)
    admin_username_or_email: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class PresetCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    video_path: Optional[str] = ""
    config_path: Optional[str] = ""
    output_dir: Optional[str] = ""


class PresetUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    video_path: Optional[str] = ""
    config_path: Optional[str] = ""
    output_dir: Optional[str] = ""


class PresetOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    video_path: Optional[str]
    config_path: Optional[str]
    output_dir: Optional[str]
    created_at: Optional[str]


class ArduinoConnectRequest(BaseModel):
    port: str = Field(..., min_length=1)


class ArduinoCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, description="e.g. IR 128, TEMP?, STATUS")


class CameraSettingRequest(BaseModel):
    setting: str
    value: Any


class ExperimentStartRequest(BaseModel):
    duration_s: int = 0
    filename_prefix: str = "exp"
    camera_list: list[str] = []
    stimuli: dict[str, Any] = {}


class AnalysisStartRequest(BaseModel):
    video_path: str
    config_path: Optional[str] = None
    output_dir: Optional[str] = None


class AppSettingsOut(BaseModel):
    zebrazoom_exe: str = ""


class AppSettingsUpdate(BaseModel):
    zebrazoom_exe: Optional[str] = None


class ZebraZoomTestRequest(BaseModel):
    path: str = Field(..., min_length=1)


class ZebraZoomBrowseOut(BaseModel):
    """Path from a native OS dialog (empty if user cancelled or dialog unavailable)."""

    path: str = ""
    native_dialog: bool = True
