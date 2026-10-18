import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import AsyncClient
import json

_db: AsyncClient | None = None


def get_db() -> AsyncClient:
    """Returns initialized Firestore async client (singleton)."""
    global _db
    if _db is None:
        _init_firebase()
    return _db


def _init_firebase():
    global _db

    # Support both file path and JSON string (for Render env vars)
    cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")

    if not firebase_admin._apps:
        if cred_json:
            # Render.com: set the entire JSON as environment variable
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        elif os.path.exists(cred_path):
            # Local development: use file
            cred = credentials.Certificate(cred_path)
        else:
            raise RuntimeError(
                "Firebase credentials not found. "
                "Set FIREBASE_SERVICE_ACCOUNT_JSON env var on Render, "
                "or place serviceAccountKey.json in backend root for local dev."
            )
        app = firebase_admin.initialize_app(cred)
    else:
        app = firebase_admin.get_app()

    # Use the initialized app's project & credentials for the async client
    try:
        from google.oauth2 import service_account
        if cred_json:
            cred_info = json.loads(cred_json)
            g_creds = service_account.Credentials.from_service_account_info(cred_info)
            _db = firestore.AsyncClient(project=cred_info.get("project_id"), credentials=g_creds)
        elif os.path.exists(cred_path):
            g_creds = service_account.Credentials.from_service_account_file(cred_path)
            _db = firestore.AsyncClient(credentials=g_creds)
        else:
            _db = firestore.AsyncClient()
    except Exception as e:
        print(f"Warning: Failed to init specialized AsyncClient: {e}, falling back to default")
        _db = firestore.AsyncClient()

