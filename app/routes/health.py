import os
from fastapi import APIRouter
from ..models.schemas import HealthResponse
from ..services.firebase_service import get_db

router = APIRouter(tags=["Health"])


@router.get("/", summary="API root")
async def root():
    return {
        "app": "PrivacyGuard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "jumble": "POST /api/v1/jumble",
            "unjumble": "POST /api/v1/unjumble",
            "verify": "POST /api/v1/verify",
            "create_session": "POST /api/v1/sessions/create",
            "session_status": "GET /api/v1/sessions/{session_id}",
            "deactivate_session": "POST /api/v1/sessions/{session_id}/deactivate",
            "user_sessions": "GET /api/v1/sessions/user/{user_id}",
        },
    }


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Check API and database connectivity."""
    import asyncio
    db_status = "disconnected"
    try:
        db = get_db()
        # Lightweight connectivity test with 3.0s timeout
        await asyncio.wait_for(db.collection("_health").document("ping").get(), timeout=3.0)
        db_status = "connected"
    except asyncio.TimeoutError:
        db_status = "timeout"
    except Exception as e:
        db_status = f"error: {str(e)[:80]}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        version="1.0.0",
        database=db_status,
        message="PrivacyGuard API is running",
    )


@router.get("/apk", summary="APK download info")
async def apk_info():
    """Returns the APK download URL for Android installation."""
    apk_url = os.getenv("APK_DOWNLOAD_URL", "")
    web_url = os.getenv("WEB_HOSTING_URL", "")
    return {
        "apk_available": bool(apk_url),
        "apk_download_url": apk_url,
        "web_page": web_url,
        "instructions": [
            "1. Open this URL on your Android phone",
            "2. Allow 'Install from unknown sources' in Settings",
            "3. Download and install PrivacyGuard.apk",
            "4. Open app, set your PIN, shake to activate!",
        ],
        "version": "1.0.0",
        "platform": "Android (APK)",
    }
