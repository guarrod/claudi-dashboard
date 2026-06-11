from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token
import os

router = APIRouter()


@router.get("/google/login-url")
def get_google_login_url():
    """Get Google OAuth login URL"""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        filename="client_secret.json",
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        redirect_uri=settings.google_redirect_uri,
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
    )

    return {"authorization_url": authorization_url, "state": state}


@router.get("/google/callback")
def google_callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_secrets_file(
            filename="client_secret.json",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            redirect_uri=settings.google_redirect_uri,
        )

        flow.fetch_token(authorization_response=f"https://localhost:8000/auth/google/callback?code={code}")

        credentials = flow.credentials

        # Get user info
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        gmail_service = build("gmail", "v1", credentials=credentials)
        profile = gmail_service.users().getProfile(userId="me").execute()

        email = profile.get("emailAddress")

        # Create or update user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                google_refresh_token=credentials.refresh_token,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.google_refresh_token = credentials.refresh_token
            db.commit()

        return {"user_id": user.id, "email": user.email, "message": "Login successful"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(email: str, db: Session = Depends(get_db)):
    """Simple login (for development)"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
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
