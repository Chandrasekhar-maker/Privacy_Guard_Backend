from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .routes import jumble, sessions, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    print("🚀 PrivacyGuard API starting up...")
    try:
        from .services.firebase_service import get_db
        get_db()
        print("✅ Firebase Firestore connected")
    except Exception as e:
        print(f"⚠️  Firebase not configured yet: {e}")
        print("   Set FIREBASE_SERVICE_ACCOUNT_JSON environment variable on Render")
    yield
    print("🛑 PrivacyGuard API shutting down...")


app = FastAPI(
    title="PrivacyGuard API",
    description="""
## 🔐 PrivacyGuard — Message Privacy API

Scramble and restore messages across any social media platform.

### Features
- **Jumble**: Scramble any text using your secret PIN (zero characters added)
- **Unjumble**: Restore scrambled text using PIN  
- **Sessions**: Track active jumble sessions with auto-expiry
- **Multi-language**: Works on English, Hindi, Emojis, Arabic, Chinese, any Unicode text

### How It Works
1. User sets a secret PIN (shared only with trusted contacts)
2. Copy message → hit Jumble → paste scrambled text in WhatsApp/Telegram
3. Only someone with your PIN can decode it using the Unjumble endpoint
4. Sessions auto-expire after your configured days — messages restore automatically

### Security
- PIN is **never stored** — only SHA-256 hash in database
- Scrambling is done via deterministic Fisher-Yates permutation seeded from SHA-256(PIN)
- Wrong PIN produces different garbage output (no error — security by design)
    """,
    version="1.0.0",
    contact={
        "name": "PrivacyGuard Support",
        "email": "support@privacyguard.app",
    },
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# ── CORS — allow Flutter app and web page to call this API ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ── Include routers ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(jumble.router)
app.include_router(sessions.router)


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": str(exc), "message": "Internal server error"},
    )
