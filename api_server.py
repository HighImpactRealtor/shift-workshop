import os
import threading
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID", "").strip()
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID", "").strip()
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET", "").strip()
ZOOM_MEETING_ID = os.getenv("ZOOM_MEETING_ID", "").strip()

zoom_session = requests.Session()
token_lock = threading.Lock()
cached_zoom_token = None
cached_zoom_token_expires_at = 0


class RegistrationRequest(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=1)
    production_goal: Optional[str] = ""
    stuck: Optional[str] = ""
    questions: Optional[str] = ""


def get_zoom_access_token(force_refresh: bool = False) -> str:
    global cached_zoom_token, cached_zoom_token_expires_at

    if not ZOOM_ACCOUNT_ID or not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Missing Zoom credentials. Check ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET."
        )

    now = time.time()

    if not force_refresh and cached_zoom_token and now < cached_zoom_token_expires_at - 60:
        return cached_zoom_token

    with token_lock:
        now = time.time()
        if not force_refresh and cached_zoom_token and now < cached_zoom_token_expires_at - 60:
            return cached_zoom_token

        response = zoom_session.post(
            "https://zoom.us/oauth/token",
            params={
                "grant_type": "account_credentials",
                "account_id": ZOOM_ACCOUNT_ID,
            },
            auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET),
            timeout=10,
        )

        if not response.ok:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": response.text}

            print(f"Zoom token error: {response.status_code} - {error_data}")

            raise HTTPException(
                status_code=500,
                detail=error_data.get("reason") or error_data.get("message") or "Could not get Zoom access token.",
            )

        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = int(token_data.get("expires_in", 3600))

        if not access_token:
            raise HTTPException(status_code=500, detail="Zoom access token missing from response.")

        cached_zoom_token = access_token
        cached_zoom_token_expires_at = time.time() + expires_in

        return cached_zoom_token


def build_zoom_payload(registration: dict) -> dict:
    zoom_payload = {
        "email": registration["email"],
        "first_name": registration["first_name"].strip(),
        "last_name": registration["last_name"].strip(),
        "phone": registration["phone"].strip(),
        "custom_questions": [],
    }

    production_goal = (registration.get("production_goal") or "").strip()
    stuck = (registration.get("stuck") or "").strip()
    questions = (registration.get("questions") or "").strip()

    if production_goal:
        zoom_payload["custom_questions"].append({
            "title": "Production goal this year",
            "value": production_goal,
        })

    if stuck:
        zoom_payload["custom_questions"].append({
            "title": "Where do you feel most stuck",
            "value": stuck,
        })

    if questions:
        zoom_payload["custom_questions"].append({
            "title": "Other questions",
            "value": questions,
        })

    return zoom_payload


def send_to_zoom_in_background(registration: dict) -> None:
    try:
        access_token = get_zoom_access_token()
        zoom_payload = build_zoom_payload(registration)

        response = zoom_session.post(
            f"https://api.zoom.us/v2/meetings/{ZOOM_MEETING_ID}/registrants",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=zoom_payload,
            timeout=12,
        )

        if response.status_code == 401:
            access_token = get_zoom_access_token(force_refresh=True)
            response = zoom_session.post(
                f"https://api.zoom.us/v2/meetings/{ZOOM_MEETING_ID}/registrants",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=zoom_payload,
                timeout=12,
            )

        if not response.ok:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": response.text}

            print(
                f"Zoom background registration failed for {registration['email']}: "
                f"{response.status_code} - {error_data}"
            )
            return

        data = response.json()
        print(
            f"Zoom registration succeeded for {registration['email']}: "
            f"registrant_id={data.get('registrant_id')}"
        )

    except Exception as error:
        print(f"Unexpected background registration error for {registration.get('email')}: {error}")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/register")
def register_user(payload: RegistrationRequest, background_tasks: BackgroundTasks):
    if not ZOOM_MEETING_ID:
        raise HTTPException(status_code=500, detail="Missing ZOOM_MEETING_ID.")

    if not ZOOM_ACCOUNT_ID or not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Missing Zoom credentials. Check ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET."
        )

    registration = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

    background_tasks.add_task(send_to_zoom_in_background, registration)

    return {
        "success": True,
        "message": "Registration received. Watch your inbox for your Zoom confirmation email.",
    }


@app.get("/")
def serve_index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/app.js")
def serve_app_js():
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")


@app.get("/base.css")
def serve_base_css():
    return FileResponse(BASE_DIR / "base.css", media_type="text/css")


@app.get("/style.css")
def serve_style_css():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/jeremy-larkin.jpeg")
def serve_jeremy_image():
    return FileResponse(BASE_DIR / "jeremy-larkin.jpeg")
