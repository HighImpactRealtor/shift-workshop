import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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


class RegistrationRequest(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=1)
    production_goal: Optional[str] = ""
    stuck: Optional[str] = ""
    questions: Optional[str] = ""


def get_zoom_access_token() -> str:
    if not ZOOM_ACCOUNT_ID or not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Missing Zoom credentials. Check ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET."
        )

    response = requests.post(
        "https://zoom.us/oauth/token",
        params={
            "grant_type": "account_credentials",
            "account_id": ZOOM_ACCOUNT_ID,
        },
        auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET),
        timeout=30,
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

    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="Zoom access token missing from response."
        )

    return access_token


@app.post("/api/register")
def register_user(payload: RegistrationRequest):
    if not ZOOM_MEETING_ID:
        raise HTTPException(
            status_code=500,
            detail="Missing ZOOM_MEETING_ID."
        )

    access_token = get_zoom_access_token()

    zoom_payload = {
        "email": payload.email,
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "phone": payload.phone.strip(),
        "custom_questions": [],
    }

    if payload.production_goal and payload.production_goal.strip():
        zoom_payload["custom_questions"].append({
            "title": "Production goal this year",
            "value": payload.production_goal.strip(),
        })

    if payload.stuck and payload.stuck.strip():
        zoom_payload["custom_questions"].append({
            "title": "Where do you feel most stuck",
            "value": payload.stuck.strip(),
        })

    if payload.questions and payload.questions.strip():
        zoom_payload["custom_questions"].append({
            "title": "Other questions",
            "value": payload.questions.strip(),
        })

    response = requests.post(
        f"https://api.zoom.us/v2/meetings/{ZOOM_MEETING_ID}/registrants",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=zoom_payload,
        timeout=30,
    )

    if not response.ok:
        try:
            error_data = response.json()
        except Exception:
            error_data = {"message": response.text}

        print(f"Zoom API error: {response.status_code} - {error_data}")

        raise HTTPException(
            status_code=response.status_code if response.status_code in (400, 401, 403, 404, 409, 429) else 422,
            detail=error_data,
        )

    data = response.json()

    return {
        "success": True,
        "message": "Registration successful.",
        "registrant_id": data.get("registrant_id"),
        "join_url": data.get("join_url"),
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


@app.get("/Image_20260304_105010_282.jpeg")
def serve_uploaded_image():
    return FileResponse(BASE_DIR / "Image_20260304_105010_282.jpeg")
