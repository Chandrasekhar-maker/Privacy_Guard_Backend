import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    SessionCreateRequest,
    SessionDeactivateRequest,
    SessionResponse,
    SessionStatusResponse,
)
from ..services.firebase_service import get_db

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])

SESSIONS_COLLECTION = "privacy_guard_sessions"


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


@router.post("/create", response_model=SessionResponse, summary="Create a new jumble session")
async def create_session(req: SessionCreateRequest):
    """
    Creates a new jumble session in Firestore.
    
    - Stores session metadata (user_id, expiry, pin_hash) in Firestore
    - PIN is stored as SHA-256 hash only — raw PIN never stored
    - Returns a session_id to track the session
    """
    db = get_db()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=req.expiry_days)

    session_data = {
        "session_id": session_id,
        "user_id": req.user_id,
        "pin_hash": req.pin_hash,  # SHA-256 of PIN only
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expiry_days": req.expiry_days,
        "is_active": True,
    }

    try:
        await db.collection(SESSIONS_COLLECTION).document(session_id).set(session_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return SessionResponse(
        success=True,
        session_id=session_id,
        user_id=req.user_id,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        expiry_days=req.expiry_days,
        is_active=True,
        message=f"Session created. Jumble active for {req.expiry_days} days.",
    )


@router.get("/{session_id}", response_model=SessionStatusResponse, summary="Get session status")
async def get_session_status(session_id: str):
    """
    Check if a session is active, expired, and how many days remain.
    """
    db = get_db()
    try:
        doc = await db.collection(SESSIONS_COLLECTION).document(session_id).get()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")

    data = doc.to_dict()
    expires_at = datetime.fromisoformat(data["expires_at"])
    now = datetime.now(timezone.utc)
    is_expired = now > expires_at
    days_remaining = max(0, (expires_at - now).days)

    # Auto-deactivate expired sessions
    if is_expired and data.get("is_active"):
        await db.collection(SESSIONS_COLLECTION).document(session_id).update({"is_active": False})
        data["is_active"] = False

    return SessionStatusResponse(
        session_id=session_id,
        is_active=data.get("is_active", False) and not is_expired,
        is_expired=is_expired,
        days_remaining=days_remaining,
        expires_at=data.get("expires_at"),
    )


@router.post("/{session_id}/deactivate", summary="Deactivate a session (requires PIN hash)")
async def deactivate_session(session_id: str, req: SessionDeactivateRequest):
    """
    Deactivate a session (restore messages to normal).
    Requires the original PIN hash for verification.
    """
    db = get_db()
    try:
        doc = await db.collection(SESSIONS_COLLECTION).document(session_id).get()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")

    data = doc.to_dict()

    # Verify PIN hash
    if data.get("pin_hash") != req.pin_hash:
        raise HTTPException(status_code=401, detail="Invalid PIN — cannot deactivate")

    await db.collection(SESSIONS_COLLECTION).document(session_id).update({"is_active": False})

    return {"success": True, "session_id": session_id, "message": "Session deactivated. Messages restored."}


@router.get("/user/{user_id}", summary="Get all sessions for a user")
async def get_user_sessions(user_id: str):
    """
    Retrieve all sessions created by a specific user ID.
    """
    db = get_db()
    try:
        query = db.collection(SESSIONS_COLLECTION).where("user_id", "==", user_id)
        docs = await query.get()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    sessions = []
    now = datetime.now(timezone.utc)
    for doc in docs:
        d = doc.to_dict()
        expires_at = datetime.fromisoformat(d["expires_at"])
        sessions.append({
            "session_id": d["session_id"],
            "created_at": d["created_at"],
            "expires_at": d["expires_at"],
            "is_active": d.get("is_active", False) and now < expires_at,
            "days_remaining": max(0, (expires_at - now).days),
        })

    return {"user_id": user_id, "total_sessions": len(sessions), "sessions": sessions}
