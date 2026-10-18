from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Request Models ─────────────────────────────────────────────────────────

class JumbleRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text to scramble")
    pin: str = Field(..., min_length=4, max_length=8, description="4-8 digit security PIN")
    user_id: Optional[str] = Field(None, description="Optional user ID to log session")


class UnjumbleRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Scrambled text to restore")
    pin: str = Field(..., min_length=4, max_length=8, description="Security PIN used to scramble")


class SessionCreateRequest(BaseModel):
    user_id: str = Field(..., description="Unique device/user identifier")
    pin_hash: str = Field(..., description="SHA-256 hash of PIN (never send raw PIN)")
    expiry_days: int = Field(7, ge=1, le=60, description="Days until auto-restore")


class SessionDeactivateRequest(BaseModel):
    session_id: str
    pin_hash: str


# ─── Response Models ─────────────────────────────────────────────────────────

class JumbleResponse(BaseModel):
    success: bool
    original_length: int
    result: str
    result_length: int
    characters_added: int = 0  # Always 0 — guaranteed
    message: str = "Text scrambled successfully"


class UnjumbleResponse(BaseModel):
    success: bool
    result: str
    message: str = "Text restored successfully"


class SessionResponse(BaseModel):
    success: bool
    session_id: str
    user_id: str
    created_at: str
    expires_at: str
    expiry_days: int
    is_active: bool
    message: str


class SessionStatusResponse(BaseModel):
    session_id: str
    is_active: bool
    is_expired: bool
    days_remaining: int
    expires_at: Optional[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    message: str
