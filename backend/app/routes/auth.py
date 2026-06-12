import os

# Allow OAuth over http://localhost (development only)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.config import settings
from app.models.user import User

router = APIRouter()

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class LoginRequest(BaseModel):
    email: str


def _google_flow():
    from google_auth_oauthlib.flow import Flow

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


@router.get("/google/connect")
def google_connect():
    """Redirect the browser to Google's consent screen to authorize Gmail access"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not configured in .env",
        )

    flow = _google_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return RedirectResponse(authorization_url)


@router.get("/google/login-url")
def get_google_login_url():
    """Get Google OAuth login URL (JSON version of /google/connect)"""
    flow = _google_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return {"authorization_url": authorization_url, "state": state}


@router.get("/google/callback")
def google_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback: store refresh token for the user"""
    try:
        from googleapiclient.discovery import build

        flow = _google_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get the Gmail address of the account that authorized access
        gmail_service = build("gmail", "v1", credentials=credentials)
        profile = gmail_service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, google_refresh_token=credentials.refresh_token)
            db.add(user)
        elif credentials.refresh_token:
            user.google_refresh_token = credentials.refresh_token
        db.commit()
        db.refresh(user)

        return HTMLResponse(
            f"""
            <html>
              <body style="font-family: -apple-system, sans-serif; text-align: center; padding-top: 80px;">
                <h1>✅ Gmail conectado</h1>
                <p>Cuenta autorizada: <b>{email}</b> (usuario #{user.id})</p>
                <p>Ya puedes cerrar esta pestaña y sincronizar desde la app.</p>
              </body>
            </html>
            """
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Simple login (for development)"""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(email=req.email)
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"user_id": user.id, "email": user.email}


@router.get("/me")
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """Get current user info"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
